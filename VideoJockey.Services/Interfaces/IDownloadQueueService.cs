using System.Collections.Generic;
using System.Threading.Tasks;
using VideoJockey.Core.Entities;

namespace VideoJockey.Services.Interfaces
{
    public interface IDownloadQueueService
    {
        Task<DownloadQueueItem> AddToQueueAsync(string url, int priority = 5);
        Task<DownloadQueueItem?> GetNextQueueItemAsync();
        Task UpdateProgressAsync(int itemId, double progress);
        Task UpdateProgressAsync(int itemId, double progress, string? downloadSpeed, string? eta);
        Task UpdateStatusAsync(int itemId, DownloadStatus status, string? errorMessage = null);
        Task<DownloadQueueItem?> GetByIdAsync(int id);
        Task MarkAsCompletedAsync(int itemId, int? videoId = null);
        Task<List<DownloadQueue>> GetPendingDownloadsAsync();
        Task<bool> RetryDownloadAsync(int queueId);
    }
}