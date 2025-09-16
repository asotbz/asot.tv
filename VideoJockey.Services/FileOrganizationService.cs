using System.Globalization;
using System.Text.RegularExpressions;
using Microsoft.Extensions.Logging;
using VideoJockey.Core.Entities;
using VideoJockey.Core.Interfaces;

namespace VideoJockey.Services;

public class FileOrganizationService : IFileOrganizationService
{
    private readonly IUnitOfWork _unitOfWork;
    private readonly ILogger<FileOrganizationService> _logger;
    private readonly string _libraryPath;
    private static readonly Regex _variablePattern = new(@"\{([^}]+)\}", RegexOptions.Compiled);

    public FileOrganizationService(
        IUnitOfWork unitOfWork,
        ILogger<FileOrganizationService> logger)
    {
        _unitOfWork = unitOfWork;
        _logger = logger;
        
        // Get library path from configuration
        var config = _unitOfWork.Configurations
            .FirstOrDefaultAsync(c => c.Key == "LibraryPath" && c.Category == "Storage")
            .GetAwaiter().GetResult();
            
        _libraryPath = config?.Value ?? Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.UserProfile),
            "VideoJockey", "Library");
            
        EnsureDirectoryExists(_libraryPath);
    }

    public async Task<string> OrganizeVideoFileAsync(
        Video video, 
        string sourceFilePath, 
        CancellationToken cancellationToken = default)
    {
        try
        {
            // Get naming pattern from configuration
            var patternConfig = await _unitOfWork.Configurations
                .FirstOrDefaultAsync(c => c.Key == "NamingPattern" && c.Category == "Organization");
                
            var pattern = patternConfig?.Value ?? "{artist_safe}/{year} - {title_safe}.{format}";
            
            // Generate the organized path
            var organizedPath = GenerateFilePath(video, pattern);
            var fullPath = Path.Combine(_libraryPath, organizedPath);
            
            // Ensure directory exists
            EnsureDirectoryExists(Path.GetDirectoryName(fullPath)!);
            
            // Move the file
            if (File.Exists(sourceFilePath))
            {
                // Handle duplicate files
                if (File.Exists(fullPath))
                {
                    fullPath = GetUniqueFilePath(fullPath);
                }
                
                await Task.Run(() => File.Move(sourceFilePath, fullPath), cancellationToken);
                _logger.LogInformation("Organized video file from {Source} to {Destination}", 
                    sourceFilePath, fullPath);
                    
                // Update video entity with new path
                video.FilePath = fullPath;
                await _unitOfWork.Videos.UpdateAsync(video);
                await _unitOfWork.SaveChangesAsync();
            }
            
            return fullPath;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error organizing video file {FilePath}", sourceFilePath);
            throw;
        }
    }

    public string GenerateFilePath(Video video, string pattern)
    {
        var result = pattern;
        
        // Replace all variables in the pattern
        result = _variablePattern.Replace(result, match =>
        {
            var variable = match.Groups[1].Value;
            return GetVariableValue(video, variable);
        });
        
        // Clean up any double slashes or spaces
        result = Regex.Replace(result, @"[/\\]+", Path.DirectorySeparatorChar.ToString());
        result = result.Trim();
        
        return result;
    }

    public bool ValidatePattern(string pattern)
    {
        if (string.IsNullOrWhiteSpace(pattern))
            return false;
            
        // Check for at least one variable
        if (!_variablePattern.IsMatch(pattern))
            return false;
            
        // Check for invalid characters outside of variables
        var withoutVariables = _variablePattern.Replace(pattern, "");
        var invalidPathChars = Path.GetInvalidPathChars()
            .Where(c => c != Path.DirectorySeparatorChar && c != Path.AltDirectorySeparatorChar);
            
        return !invalidPathChars.Any(c => withoutVariables.Contains(c));
    }

    public Dictionary<string, string> GetAvailablePatternVariables()
    {
        return new Dictionary<string, string>(FileOrganizationPatternVariables.Variables);
    }

    public string PreviewOrganizedPath(Video video, string pattern)
    {
        return Path.Combine(_libraryPath, GenerateFilePath(video, pattern));
    }

    public async Task<ReorganizeResult> ReorganizeLibraryAsync(
        string newPattern, 
        IProgress<ReorganizeProgress>? progress = null, 
        CancellationToken cancellationToken = default)
    {
        var result = new ReorganizeResult();
        var startTime = DateTime.UtcNow;
        
        try
        {
            // Validate the pattern
            if (!ValidatePattern(newPattern))
            {
                result.Errors.Add("Invalid naming pattern");
                return result;
            }
            
            // Get all videos
            var videos = await _unitOfWork.Videos.GetAllAsync();
            result.TotalVideos = videos.Count();
            
            var currentIndex = 0;
            foreach (var video in videos)
            {
                if (cancellationToken.IsCancellationRequested)
                    break;
                    
                currentIndex++;
                
                // Report progress
                progress?.Report(new ReorganizeProgress
                {
                    Current = currentIndex,
                    Total = result.TotalVideos,
                    CurrentFile = video.Title ?? "Unknown"
                });
                
                try
                {
                    // Generate new path
                    var newRelativePath = GenerateFilePath(video, newPattern);
                    var newFullPath = Path.Combine(_libraryPath, newRelativePath);
                    
                    // Skip if file is already at the correct location
                    if (string.Equals(video.FilePath, newFullPath, StringComparison.OrdinalIgnoreCase))
                    {
                        result.SuccessfulMoves++;
                        continue;
                    }
                    
                    // Move the file
                    if (await MoveVideoFileAsync(video, newFullPath, cancellationToken))
                    {
                        result.SuccessfulMoves++;
                    }
                    else
                    {
                        result.FailedMoves++;
                        result.Errors.Add($"Failed to move: {video.Title}");
                    }
                }
                catch (Exception ex)
                {
                    result.FailedMoves++;
                    result.Errors.Add($"Error with {video.Title}: {ex.Message}");
                    _logger.LogError(ex, "Error reorganizing video {VideoId}", video.Id);
                }
            }
            
            // Save the new pattern to configuration
            var patternConfig = await _unitOfWork.Configurations
                .FirstOrDefaultAsync(c => c.Key == "NamingPattern" && c.Category == "Organization");
                
            if (patternConfig != null)
            {
                patternConfig.Value = newPattern;
                patternConfig.UpdatedAt = DateTime.UtcNow;
                await _unitOfWork.Configurations.UpdateAsync(patternConfig);
            }
            else
            {
                await _unitOfWork.Configurations.AddAsync(new Configuration
                {
                    Key = "NamingPattern",
                    Value = newPattern,
                    Category = "Organization",
                    Description = "File naming pattern for organized videos"
                });
            }
            
            await _unitOfWork.SaveChangesAsync();
            
            result.Duration = DateTime.UtcNow - startTime;
            return result;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error reorganizing library");
            result.Errors.Add($"Fatal error: {ex.Message}");
            result.Duration = DateTime.UtcNow - startTime;
            return result;
        }
    }

    public async Task<bool> MoveVideoFileAsync(
        Video video, 
        string newPath, 
        CancellationToken cancellationToken = default)
    {
        try
        {
            if (string.IsNullOrWhiteSpace(video.FilePath) || !File.Exists(video.FilePath))
            {
                _logger.LogWarning("Source file not found for video {VideoId}: {FilePath}", 
                    video.Id, video.FilePath);
                return false;
            }
            
            // Ensure destination directory exists
            EnsureDirectoryExists(Path.GetDirectoryName(newPath)!);
            
            // Handle duplicate files
            if (File.Exists(newPath))
            {
                newPath = GetUniqueFilePath(newPath);
            }
            
            // Move the file
            await Task.Run(() => File.Move(video.FilePath, newPath), cancellationToken);
            
            // Update the video entity
            video.FilePath = newPath;
            video.UpdatedAt = DateTime.UtcNow;
            await _unitOfWork.Videos.UpdateAsync(video);
            await _unitOfWork.SaveChangesAsync();
            
            _logger.LogInformation("Moved video file from {OldPath} to {NewPath}", 
                video.FilePath, newPath);
            
            return true;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error moving video file from {OldPath} to {NewPath}", 
                video.FilePath, newPath);
            return false;
        }
    }

    public void EnsureDirectoryExists(string filePath)
    {
        var directory = Path.GetDirectoryName(filePath);
        if (!string.IsNullOrEmpty(directory) && !Directory.Exists(directory))
        {
            Directory.CreateDirectory(directory);
            _logger.LogDebug("Created directory: {Directory}", directory);
        }
    }

    private string GetVariableValue(Video video, string variable)
    {
        return variable.ToLowerInvariant() switch
        {
            // Artist variables
            "artist" => video.Artist ?? "Unknown Artist",
            "artist_safe" => FileOrganizationPatternVariables.MakeFileSystemSafe(video.Artist ?? "Unknown Artist"),
            "artist_sort" => video.Artist ?? "Unknown Artist", // Use Artist as no separate ArtistSort field
            
            // Title variables
            "title" => video.Title ?? "Unknown Title",
            "title_safe" => FileOrganizationPatternVariables.MakeFileSystemSafe(video.Title ?? "Unknown Title"),
            
            // Date variables
            "year" => video.Year?.ToString("0000") ?? "0000",
            "year2" => (video.Year % 100)?.ToString("00") ?? "00",
            "month" => "00", // No separate month field
            "month_name" => "Unknown", // No separate month field
            "day" => "00", // No separate day field
            "date" => video.Year != null ? $"{video.Year:0000}-01-01" : "0000-00-00",
            
            // Genre variables
            "genre" => video.Genres?.FirstOrDefault()?.Name ?? "Unknown",
            "genres" => string.Join(", ", video.Genres?.Select(g => g.Name) ?? new[] { "Unknown" }),
            
            // Label variables  
            "label" => video.Publisher ?? "Unknown Label",
            "label_safe" => FileOrganizationPatternVariables.MakeFileSystemSafe(video.Publisher ?? "Unknown Label"),
            
            // Technical variables
            "resolution" => GetResolutionString(ParseHeight(video.Resolution)),
            "width" => ParseWidth(video.Resolution)?.ToString() ?? "0",
            "height" => ParseHeight(video.Resolution)?.ToString() ?? "0",
            "codec" => video.VideoCodec ?? "unknown",
            "format" => Path.GetExtension(video.FilePath ?? ".mp4").TrimStart('.'),
            "bitrate" => video.Bitrate?.ToString() ?? "0",
            "fps" => video.FrameRate?.ToString("F2") ?? "0",
            
            // IMVDb variables
            "imvdb_id" => video.ImvdbId?.ToString() ?? "",
            "director" => video.Director ?? "Unknown",
            "production" => video.ProductionCompany ?? "Unknown",
            "featured_artists" => string.Join(", ", video.FeaturedArtists?.Select(fa => fa.Name) ?? Enumerable.Empty<string>()),
            
            // MusicBrainz variables
            "mb_artist_id" => "", // Not in current Video entity
            "mb_recording_id" => video.MusicBrainzRecordingId ?? "",
            "album" => video.Album ?? "Unknown Album",
            "track_number" => "", // Not in current Video entity
            
            // Custom variables
            "tags" => string.Join(", ", video.Tags?.Select(t => t.Name) ?? new[] { "Unknown" }),
            "collection" => "", // Not in current Video entity
            "custom1" => "", // Not in current Video entity
            "custom2" => "", // Not in current Video entity
            "custom3" => "", // Not in current Video entity
            
            // Default
            _ => $"{{{variable}}}"
        };
    }

    private string GetResolutionString(int? height)
    {
        return height switch
        {
            >= 2160 => "4K",
            >= 1440 => "1440p",
            >= 1080 => "1080p",
            >= 720 => "720p",
            >= 480 => "480p",
            >= 360 => "360p",
            >= 240 => "240p",
            _ => "SD"
        };
    }

    private string GetUniqueFilePath(string filePath)
    {
        var directory = Path.GetDirectoryName(filePath)!;
        var fileNameWithoutExtension = Path.GetFileNameWithoutExtension(filePath);
        var extension = Path.GetExtension(filePath);
        
        var counter = 1;
        string uniquePath;
        
        do
        {
            uniquePath = Path.Combine(directory, $"{fileNameWithoutExtension}_{counter}{extension}");
            counter++;
        } while (File.Exists(uniquePath));
        
        return uniquePath;
    }

    private int? ParseHeight(string? resolution)
    {
        if (string.IsNullOrEmpty(resolution))
            return null;
            
        var parts = resolution.Split('x');
        if (parts.Length == 2 && int.TryParse(parts[1], out var height))
            return height;
            
        return null;
    }

    private int? ParseWidth(string? resolution)
    {
        if (string.IsNullOrEmpty(resolution))
            return null;
            
        var parts = resolution.Split('x');
        if (parts.Length == 2 && int.TryParse(parts[0], out var width))
            return width;
            
        return null;
    }
}