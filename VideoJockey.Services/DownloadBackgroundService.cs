using System;
using System.IO;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using VideoJockey.Core.Entities;
using VideoJockey.Core.Interfaces;
using VideoJockey.Services.Interfaces;
using DownloadStatusEnum = VideoJockey.Core.Entities.DownloadStatus;

namespace VideoJockey.Services
{
    public class DownloadBackgroundService : BackgroundService
    {
        private readonly IServiceScopeFactory _scopeFactory;
        private readonly ILogger<DownloadBackgroundService> _logger;
        private readonly SemaphoreSlim _downloadSemaphore;
        private const int MaxConcurrentDownloads = 2;

        public DownloadBackgroundService(
            IServiceScopeFactory scopeFactory,
            ILogger<DownloadBackgroundService> logger)
        {
            _scopeFactory = scopeFactory;
            _logger = logger;
            _downloadSemaphore = new SemaphoreSlim(MaxConcurrentDownloads, MaxConcurrentDownloads);
        }

        protected override async Task ExecuteAsync(CancellationToken stoppingToken)
        {
            _logger.LogInformation("Download Background Service started");

            while (!stoppingToken.IsCancellationRequested)
            {
                try
                {
                    await ProcessDownloadQueue(stoppingToken);
                    await Task.Delay(TimeSpan.FromSeconds(5), stoppingToken);
                }
                catch (OperationCanceledException)
                {
                    // Expected when cancellation is requested
                    break;
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "Error in download background service");
                    await Task.Delay(TimeSpan.FromSeconds(30), stoppingToken);
                }
            }

            _logger.LogInformation("Download Background Service stopped");
        }

        private async Task ProcessDownloadQueue(CancellationToken cancellationToken)
        {
            using var scope = _scopeFactory.CreateScope();
            var downloadQueueService = scope.ServiceProvider.GetRequiredService<VideoJockey.Services.Interfaces.IDownloadQueueService>();
            var ytDlpService = scope.ServiceProvider.GetRequiredService<IYtDlpService>();

            var pendingDownloads = await downloadQueueService.GetPendingDownloadsAsync();

            var downloadTasks = pendingDownloads.Select(download => 
                ProcessDownload(download.Id.GetHashCode(), cancellationToken));

            await Task.WhenAll(downloadTasks);
        }

        private async Task ProcessDownload(int queueId, CancellationToken cancellationToken)
        {
            await _downloadSemaphore.WaitAsync(cancellationToken);
            
            try
            {
                using var scope = _scopeFactory.CreateScope();
                var downloadQueueService = scope.ServiceProvider.GetRequiredService<VideoJockey.Services.Interfaces.IDownloadQueueService>();
                var ytDlpService = scope.ServiceProvider.GetRequiredService<IYtDlpService>();
                var unitOfWork = scope.ServiceProvider.GetRequiredService<IUnitOfWork>();

                // Get the queue item - need to handle Guid to int conversion
                var queueItems = await unitOfWork.DownloadQueueItems
                    .GetAsync(q => q.Id.GetHashCode() == queueId);
                var queueItem = queueItems.FirstOrDefault();
                
                if (queueItem == null || queueItem.Status != DownloadStatusEnum.Queued)
                {
                    return;
                }

                _logger.LogInformation("Starting download for queue item {QueueId}: {Url}", 
                    queueId, queueItem.Url);

                // Update status to downloading
                await downloadQueueService.UpdateStatusAsync(
                    queueId, 
                    DownloadStatusEnum.Downloading);

                // Create progress reporter
                var progress = new Progress<Core.Interfaces.DownloadProgress>(async p =>
                {
                    await downloadQueueService.UpdateProgressAsync(
                        queueId, 
                        p.Percentage, 
                        p.DownloadSpeed, 
                        p.ETA);
                });

                // Download the video
                var result = await ytDlpService.DownloadVideoAsync(
                    queueItem.Url,
                    queueItem.OutputPath ?? "downloads",
                    progress,
                    cancellationToken);

                if (result.Success)
                {
                    // Update the queue item with the file path
                    queueItem.FilePath = result.FilePath;
                    
                    // Create video entity
                    await CreateVideoEntity(scope, result, queueItem);

                    // Mark as completed
                    await downloadQueueService.UpdateStatusAsync(
                        queueId,
                        DownloadStatusEnum.Completed);

                    _logger.LogInformation("Successfully downloaded video for queue item {QueueId}", queueId);
                }
                else
                {
                    // Check if we should retry
                    if (queueItem.RetryCount < 3)
                    {
                        await downloadQueueService.RetryDownloadAsync(queueId);
                        _logger.LogWarning("Download failed for queue item {QueueId}, will retry. Error: {Error}", 
                            queueId, result.ErrorMessage);
                    }
                    else
                    {
                        await downloadQueueService.UpdateStatusAsync(
                            queueId,
                            DownloadStatusEnum.Failed,
                            result.ErrorMessage);
                        
                        _logger.LogError("Download permanently failed for queue item {QueueId} after {RetryCount} retries. Error: {Error}", 
                            queueId, queueItem.RetryCount, result.ErrorMessage);
                    }
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error processing download for queue item {QueueId}", queueId);
                
                using var scope = _scopeFactory.CreateScope();
                var downloadQueueService = scope.ServiceProvider.GetRequiredService<VideoJockey.Services.Interfaces.IDownloadQueueService>();
                
                await downloadQueueService.UpdateStatusAsync(
                    queueId,
                    DownloadStatusEnum.Failed,
                    ex.Message);
            }
            finally
            {
                _downloadSemaphore.Release();
            }
        }

        private async Task CreateVideoEntity(
            IServiceScope scope,
            Core.Interfaces.DownloadResult result,
            DownloadQueueItem queueItem)
        {
            try
            {
                var unitOfWork = scope.ServiceProvider.GetRequiredService<IUnitOfWork>();
                var ytDlpService = scope.ServiceProvider.GetRequiredService<IYtDlpService>();

                // Get metadata for the video
                var metadata = await ytDlpService.GetVideoMetadataAsync(queueItem.Url);

                if (metadata != null)
                {
                    var video = new Video
                    {
                        Title = metadata.Title ?? Path.GetFileNameWithoutExtension(result.FilePath),
                        Artist = metadata.Channel ?? "Unknown Artist",
                        FilePath = result.FilePath,
                        Duration = metadata.Duration.HasValue ? (int)metadata.Duration.Value.TotalSeconds : (int?)null,
                        YouTubeId = metadata.Id,
                        Description = metadata.Description,
                        ImportedAt = DateTime.UtcNow
                    };

                    // Extract resolution if available
                    if (metadata.Width.HasValue && metadata.Height.HasValue)
                    {
                        video.Resolution = $"{metadata.Width}x{metadata.Height}";
                    }

                    // Check if video already exists
                    var existingVideo = await unitOfWork.Videos
                        .FirstOrDefaultAsync(v => v.YouTubeId == metadata.Id);

                    if (existingVideo == null)
                    {
                        await unitOfWork.Videos.AddAsync(video);
                        await unitOfWork.SaveChangesAsync();
                        
                        _logger.LogInformation("Created video entity for: {Title}", video.Title);
                    }
                    else
                    {
                        // Update existing video
                        existingVideo.FilePath = result.FilePath;
                        existingVideo.ImportedAt = DateTime.UtcNow;
                        await unitOfWork.Videos.UpdateAsync(existingVideo);
                        await unitOfWork.SaveChangesAsync();
                        
                        _logger.LogInformation("Updated existing video entity for: {Title}", existingVideo.Title);
                    }
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error creating video entity");
                // Don't throw - we don't want to fail the download just because we couldn't create the entity
            }
        }

        public override async Task StopAsync(CancellationToken cancellationToken)
        {
            _logger.LogInformation("Download Background Service is stopping");
            await base.StopAsync(cancellationToken);
            _downloadSemaphore?.Dispose();
        }
    }
}