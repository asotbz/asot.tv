using System.Text;
using System.Xml;
using System.Xml.Linq;
using VideoJockey.Core.Entities;
using VideoJockey.Services.Interfaces;

namespace VideoJockey.Services
{
    public class NfoExportService : INfoExportService
    {
        public async Task<bool> ExportNfoAsync(Video video, string outputPath)
        {
            try
            {
                var nfoContent = GenerateNfoContent(video);
                await File.WriteAllTextAsync(outputPath, nfoContent);
                return true;
            }
            catch (Exception)
            {
                return false;
            }
        }

        public async Task<int> BulkExportNfoAsync(IEnumerable<Video> videos, string outputDirectory, bool useVideoPath = false)
        {
            int successCount = 0;
            
            foreach (var video in videos)
            {
                string outputPath;
                
                if (useVideoPath && !string.IsNullOrEmpty(video.FilePath))
                {
                    // Export NFO next to video file
                    outputPath = Path.ChangeExtension(video.FilePath, ".nfo");
                }
                else
                {
                    // Export to specified directory
                    var filename = SanitizeFileName($"{video.Artist} - {video.Title}.nfo");
                    outputPath = Path.Combine(outputDirectory, filename);
                }

                if (await ExportNfoAsync(video, outputPath))
                {
                    successCount++;
                }
            }
            
            return successCount;
        }

        public string GenerateNfoContent(Video video)
        {
            var settings = new XmlWriterSettings
            {
                Indent = true,
                IndentChars = "    ",
                Encoding = Encoding.UTF8,
                OmitXmlDeclaration = false
            };

            using var stringWriter = new StringWriter();
            using var xmlWriter = XmlWriter.Create(stringWriter, settings);

            // Start document
            xmlWriter.WriteStartDocument();
            xmlWriter.WriteStartElement("musicvideo");

            // Basic information
            WriteElement(xmlWriter, "title", video.Title);
            WriteElement(xmlWriter, "artist", video.Artist);
            WriteElement(xmlWriter, "album", video.Album);
            WriteElement(xmlWriter, "year", video.Year?.ToString());
            
            // Additional metadata
            WriteElement(xmlWriter, "runtime", video.Duration?.ToString());
            WriteElement(xmlWriter, "director", video.Director);
            WriteElement(xmlWriter, "studio", video.ProductionCompany);
            WriteElement(xmlWriter, "publisher", video.Publisher);
            
            // Plot/Description
            WriteElement(xmlWriter, "plot", video.Description);
            WriteElement(xmlWriter, "outline", video.Description);
            
            // Technical details
            WriteElement(xmlWriter, "format", video.Format);
            WriteElement(xmlWriter, "videocodec", video.VideoCodec);
            WriteElement(xmlWriter, "audiocodec", video.AudioCodec);
            WriteElement(xmlWriter, "resolution", video.Resolution);
            
            // Parse resolution to get width and height if available
            if (!string.IsNullOrEmpty(video.Resolution))
            {
                var resParts = video.Resolution.Split('x');
                if (resParts.Length == 2)
                {
                    if (int.TryParse(resParts[0], out var width))
                        WriteElement(xmlWriter, "width", width.ToString());
                    if (int.TryParse(resParts[1], out var height))
                        WriteElement(xmlWriter, "height", height.ToString());
                }
            }
            
            WriteElement(xmlWriter, "framerate", video.FrameRate?.ToString());
            WriteElement(xmlWriter, "filesize", video.FileSize?.ToString());
            WriteElement(xmlWriter, "bitrate", video.Bitrate?.ToString());
            
            // Identifiers
            WriteElement(xmlWriter, "imvdbid", video.ImvdbId);
            WriteElement(xmlWriter, "mbid", video.MusicBrainzRecordingId);
            WriteElement(xmlWriter, "youtubeid", video.YouTubeId);
            
            // Rating
            if (video.Rating.HasValue)
            {
                xmlWriter.WriteStartElement("rating");
                WriteElement(xmlWriter, "value", (video.Rating.Value * 2).ToString("F1")); // Convert 1-5 to 1-10 scale
                WriteElement(xmlWriter, "max", "10");
                xmlWriter.WriteEndElement();
            }
            
            // Genres
            if (video.Genres?.Any() == true)
            {
                foreach (var genre in video.Genres)
                {
                    WriteElement(xmlWriter, "genre", genre.Name);
                }
            }
            
            // Tags
            if (video.Tags?.Any() == true)
            {
                foreach (var tag in video.Tags)
                {
                    WriteElement(xmlWriter, "tag", tag.Name);
                }
            }
            
            // Featured artists (as actors for compatibility)
            if (video.FeaturedArtists?.Any() == true)
            {
                foreach (var artist in video.FeaturedArtists)
                {
                    xmlWriter.WriteStartElement("actor");
                    WriteElement(xmlWriter, "name", artist.Name);
                    WriteElement(xmlWriter, "role", "Featured Artist");
                    WriteElement(xmlWriter, "type", "FeaturedArtist");
                    if (!string.IsNullOrEmpty(artist.ImvdbArtistId))
                        WriteElement(xmlWriter, "imvdbartistid", artist.ImvdbArtistId);
                    if (!string.IsNullOrEmpty(artist.MusicBrainzArtistId))
                        WriteElement(xmlWriter, "mbartistid", artist.MusicBrainzArtistId);
                    xmlWriter.WriteEndElement();
                }
            }
            
            // File information
            xmlWriter.WriteStartElement("fileinfo");
            xmlWriter.WriteStartElement("streamdetails");
            
            // Video stream
            xmlWriter.WriteStartElement("video");
            WriteElement(xmlWriter, "codec", video.VideoCodec);
            
            // Parse resolution for aspect ratio and dimensions
            if (!string.IsNullOrEmpty(video.Resolution))
            {
                var resParts = video.Resolution.Split('x');
                if (resParts.Length == 2)
                {
                    if (int.TryParse(resParts[0], out var width) && int.TryParse(resParts[1], out var height))
                    {
                        WriteElement(xmlWriter, "width", width.ToString());
                        WriteElement(xmlWriter, "height", height.ToString());
                        
                        // Calculate aspect ratio
                        var gcd = GetGCD(width, height);
                        var aspectWidth = width / gcd;
                        var aspectHeight = height / gcd;
                        WriteElement(xmlWriter, "aspect", $"{aspectWidth}:{aspectHeight}");
                    }
                }
            }
            
            WriteElement(xmlWriter, "durationinseconds", video.Duration?.ToString());
            WriteElement(xmlWriter, "framerate", video.FrameRate?.ToString("F2"));
            xmlWriter.WriteEndElement(); // video
            
            // Audio stream
            xmlWriter.WriteStartElement("audio");
            WriteElement(xmlWriter, "codec", video.AudioCodec);
            WriteElement(xmlWriter, "bitrate", video.Bitrate?.ToString());
            xmlWriter.WriteEndElement(); // audio
            
            xmlWriter.WriteEndElement(); // streamdetails
            xmlWriter.WriteEndElement(); // fileinfo
            
            // Custom VideoJockey fields
            xmlWriter.WriteStartElement("videojockey");
            WriteElement(xmlWriter, "dateadded", video.CreatedAt.ToString("yyyy-MM-dd HH:mm:ss"));
            WriteElement(xmlWriter, "dateimported", video.ImportedAt?.ToString("yyyy-MM-dd HH:mm:ss"));
            WriteElement(xmlWriter, "lastplayed", video.LastPlayedAt?.ToString("yyyy-MM-dd HH:mm:ss"));
            WriteElement(xmlWriter, "playcount", video.PlayCount.ToString());
            WriteElement(xmlWriter, "filepath", video.FilePath);
            WriteElement(xmlWriter, "thumbnailpath", video.ThumbnailPath);
            WriteElement(xmlWriter, "nfopath", video.NfoPath);
            xmlWriter.WriteEndElement(); // videojockey
            
            // Thumbnail/poster
            if (!string.IsNullOrEmpty(video.ThumbnailPath))
            {
                WriteElement(xmlWriter, "thumb", video.ThumbnailPath);
                WriteElement(xmlWriter, "poster", video.ThumbnailPath);
            }
            
            // End document
            xmlWriter.WriteEndElement(); // musicvideo
            xmlWriter.WriteEndDocument();
            xmlWriter.Flush();

            return stringWriter.ToString();
        }

        private void WriteElement(XmlWriter writer, string elementName, string? value)
        {
            if (!string.IsNullOrWhiteSpace(value))
            {
                writer.WriteElementString(elementName, value);
            }
        }

        private string SanitizeFileName(string filename)
        {
            var invalidChars = Path.GetInvalidFileNameChars();
            var sanitized = new StringBuilder(filename.Length);
            
            foreach (char c in filename)
            {
                if (Array.IndexOf(invalidChars, c) < 0)
                {
                    sanitized.Append(c);
                }
                else
                {
                    sanitized.Append('_');
                }
            }
            
            return sanitized.ToString();
        }

        private int GetGCD(int a, int b)
        {
            while (b != 0)
            {
                int temp = b;
                b = a % b;
                a = temp;
            }
            return a;
        }
    }
}