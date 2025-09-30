using VideoJockey.Core.Entities;

namespace VideoJockey.Core.Specifications.DownloadQueue;

public sealed class DownloadQueueActiveSpecification : BaseSpecification<DownloadQueueItem>
{
    public DownloadQueueActiveSpecification()
    {
        ApplyCriteria(item =>
            (item.Status == DownloadStatus.Queued || item.Status == DownloadStatus.Downloading) &&
            !item.IsDeleted);

        AddOrderBy(item => item.Priority);
        AddOrderBy(item => item.CreatedAt);
        EnableTracking();
    }
}
