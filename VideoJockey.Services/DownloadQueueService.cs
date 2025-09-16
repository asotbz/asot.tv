using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using VideoJockey.Core.Entities;
using VideoJockey.Core.Interfaces;

namespace VideoJockey.Services
{
    public class DownloadQueueService : IDownloadQueueService
    {
        private readonly IUnitOfWork _unitOfWork;
        private readonly ILogger<DownloadQueueService> _logger;
        
        public DownloadQueueService(IUnitOfWork unitOfWork, ILogger<DownloadQueueService> logger)
        {
            _unitOfWork = unitOfWork;
            _logger = logger;
        }
        
        public async Task<DownloadQueue> AddToQueueAsync(
            string url, 
            string outputPath,
            string? format = null,
            int priority = 0)
        {
            try
            {
                var queueItem = new DownloadQueue
                {
                    Url = url,
                    OutputPath = outputPath,
                    Format = format,
                    Priority = priority,
                    Status = Core.Interfaces.DownloadStatus.Pending.ToString(),
                    AddedDate = DateTime.UtcNow,
                    RetryCount = 0,
                    IsDeleted = false
                };
                
                await _unitOfWork.DownloadQueues.AddAsync(queueItem);
                await _unitOfWork.SaveChangesAsync();
                
                _logger.LogInformation("Added URL to download queue: {Url}", url);
                return queueItem;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error adding URL to queue: {Url}", url);
                throw;
            }
        }
        
        public async Task<DownloadQueue> AddToQueueAsync(
            string url, 
            string? customTitle = null,
            int priority = 0)
        {
            // Overload for backward compatibility
            return await AddToQueueAsync(url, "downloads", null, priority);
        }
        
        public async Task<List<DownloadQueue>> GetPendingDownloadsAsync()
        {
            try
            {
                var items = await _unitOfWork.DownloadQueues
                    .GetAsync(q => !q.IsDeleted &&
                        (q.Status == Core.Interfaces.DownloadStatus.Pending.ToString() ||
                         q.Status == Core.Interfaces.DownloadStatus.Failed.ToString()));
                
                return items.ToList();
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error getting pending downloads");
                throw;
            }
        }
        
        public async Task<IEnumerable<DownloadQueue>> GetActiveDownloadsAsync()
        {
            try
            {
                return await _unitOfWork.DownloadQueues
                    .GetAsync(q => !q.IsDeleted &&
                        q.Status == Core.Interfaces.DownloadStatus.Downloading.ToString());
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error getting active downloads");
                throw;
            }
        }
        
        public async Task<IEnumerable<DownloadQueue>> GetQueueHistoryAsync(
            int pageNumber = 1,
            int pageSize = 50)
        {
            try
            {
                // Use GetAsync with ordering and paging logic
                var allItems = await _unitOfWork.DownloadQueues
                    .GetAsync(q => !q.IsDeleted &&
                        (q.Status == Core.Interfaces.DownloadStatus.Completed.ToString() ||
                         q.Status == Core.Interfaces.DownloadStatus.Failed.ToString()));
                
                return allItems
                    .OrderByDescending(q => q.CompletedDate ?? q.StartedDate ?? q.AddedDate)
                    .Skip((pageNumber - 1) * pageSize)
                    .Take(pageSize)
                    .ToList();
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error getting queue history");
                throw;
            }
        }
        
        public async Task UpdateQueueItemStatusAsync(
            int queueId,
            Core.Interfaces.DownloadStatus status,
            string? errorMessage = null)
        {
            try
            {
                // Convert int to Guid for lookup - or we need to update the interface
                var items = await _unitOfWork.DownloadQueues.GetAsync(q => q.Id == new Guid(queueId.ToString("D32")));
                var item = items.FirstOrDefault();
                
                if (item != null)
                {
                    item.Status = status.ToString();
                    item.ErrorMessage = errorMessage;
                    
                    if (status == Core.Interfaces.DownloadStatus.Downloading)
                    {
                        item.StartedDate = DateTime.UtcNow;
                    }
                    else if (status == Core.Interfaces.DownloadStatus.Completed ||
                             status == Core.Interfaces.DownloadStatus.Failed)
                    {
                        item.CompletedDate = DateTime.UtcNow;
                    }
                    
                    await _unitOfWork.DownloadQueues.UpdateAsync(item);
                    await _unitOfWork.SaveChangesAsync();
                    _logger.LogInformation("Updated queue item {Id} status to {Status}", queueId, status);
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error updating queue item status: {Id}", queueId);
                throw;
            }
        }
        
        public async Task UpdateProgressAsync(
            int queueId,
            double progress,
            string? downloadSpeed = null,
            string? eta = null)
        {
            try
            {
                var items = await _unitOfWork.DownloadQueues.GetAsync(q => q.Id == new Guid(queueId.ToString("D32")));
                var item = items.FirstOrDefault();
                
                if (item != null)
                {
                    item.Progress = progress;
                    item.DownloadSpeed = downloadSpeed;
                    item.ETA = eta;
                    await _unitOfWork.DownloadQueues.UpdateAsync(item);
                    await _unitOfWork.SaveChangesAsync();
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error updating queue item progress: {Id}", queueId);
                throw;
            }
        }
        
        public async Task<bool> RemoveFromQueueAsync(int queueId)
        {
            try
            {
                var items = await _unitOfWork.DownloadQueues.GetAsync(q => q.Id == new Guid(queueId.ToString("D32")));
                var item = items.FirstOrDefault();
                
                if (item != null && item.Status != Core.Interfaces.DownloadStatus.Downloading.ToString())
                {
                    item.IsDeleted = true;
                    item.DeletedDate = DateTime.UtcNow;
                    await _unitOfWork.DownloadQueues.UpdateAsync(item);
                    await _unitOfWork.SaveChangesAsync();
                    _logger.LogInformation("Removed queue item: {Id}", queueId);
                    return true;
                }
                return false;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error removing queue item: {Id}", queueId);
                throw;
            }
        }
        
        public async Task<bool> RetryFailedDownloadAsync(int queueId)
        {
            try
            {
                var items = await _unitOfWork.DownloadQueues.GetAsync(q => q.Id == new Guid(queueId.ToString("D32")));
                var item = items.FirstOrDefault();
                
                if (item != null && item.Status == Core.Interfaces.DownloadStatus.Failed.ToString())
                {
                    item.Status = Core.Interfaces.DownloadStatus.Pending.ToString();
                    item.RetryCount++;
                    item.ErrorMessage = null;
                    item.StartedDate = null;
                    item.CompletedDate = null;
                    item.Progress = 0;
                    await _unitOfWork.DownloadQueues.UpdateAsync(item);
                    await _unitOfWork.SaveChangesAsync();
                    
                    _logger.LogInformation("Retrying download {QueueId} (attempt #{RetryCount})", 
                        queueId, item.RetryCount);
                    return true;
                }
                return false;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error retrying download: {Id}", queueId);
                throw;
            }
        }
        
        public async Task<int> ClearCompletedAsync()
        {
            try
            {
                var completed = await _unitOfWork.DownloadQueues
                    .GetAsync(q => !q.IsDeleted &&
                        q.Status == Core.Interfaces.DownloadStatus.Completed.ToString());
                
                var count = completed.Count();
                
                foreach (var item in completed)
                {
                    item.IsDeleted = true;
                    item.DeletedDate = DateTime.UtcNow;
                    await _unitOfWork.DownloadQueues.UpdateAsync(item);
                }
                
                await _unitOfWork.SaveChangesAsync();
                _logger.LogInformation("Cleared {Count} completed downloads", count);
                
                return count;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error clearing completed items from queue");
                throw;
            }
        }
        
        public async Task<int> GetQueuePositionAsync(int queueId)
        {
            try
            {
                var items = await _unitOfWork.DownloadQueues.GetAsync(q => q.Id == new Guid(queueId.ToString("D32")));
                var item = items.FirstOrDefault();
                
                if (item == null || item.IsDeleted)
                    return -1;
                
                var pendingItems = await _unitOfWork.DownloadQueues
                    .GetAsync(q => !q.IsDeleted &&
                        q.Status == Core.Interfaces.DownloadStatus.Pending.ToString());
                
                var orderedItems = pendingItems
                    .OrderByDescending(q => q.Priority)
                    .ThenBy(q => q.AddedDate)
                    .ToList();
                
                var position = orderedItems.FindIndex(q => q.Id == item.Id);
                return position + 1; // 1-based position
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error getting queue position: {Id}", queueId);
                throw;
            }
        }
        
        public async Task<IEnumerable<DownloadQueue>> GetAllQueuedItemsAsync()
        {
            try
            {
                return await _unitOfWork.DownloadQueues
                    .GetAsync(q => !q.IsDeleted);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error getting all queued items");
                throw;
            }
        }
        
        // Additional methods for compatibility
        public async Task<List<DownloadQueue>> GetQueueAsync(bool includeCompleted = false)
        {
            try
            {
                var items = await _unitOfWork.DownloadQueues
                    .GetAsync(q => !q.IsDeleted &&
                        (includeCompleted || (q.Status != Core.Interfaces.DownloadStatus.Completed.ToString() && 
                                              q.Status != Core.Interfaces.DownloadStatus.Failed.ToString())));
                
                return items
                    .OrderByDescending(q => q.Priority)
                    .ThenBy(q => q.AddedDate)
                    .ToList();
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error getting download queue");
                throw;
            }
        }
        
        public async Task UpdateStatusAsync(int queueId, Core.Interfaces.DownloadStatus status, string? errorMessage = null)
        {
            await UpdateQueueItemStatusAsync(queueId, status, errorMessage);
        }
        
        public async Task<bool> RetryDownloadAsync(int queueId)
        {
            return await RetryFailedDownloadAsync(queueId);
        }
        
        public async Task<DownloadQueue?> GetNextDownloadAsync()
        {
            try
            {
                var items = await _unitOfWork.DownloadQueues
                    .GetAsync(q => !q.IsDeleted && q.Status == Core.Interfaces.DownloadStatus.Pending.ToString());
                
                return items
                    .OrderByDescending(q => q.Priority)
                    .ThenBy(q => q.AddedDate)
                    .FirstOrDefault();
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error getting next download");
                throw;
            }
        }
    }
}