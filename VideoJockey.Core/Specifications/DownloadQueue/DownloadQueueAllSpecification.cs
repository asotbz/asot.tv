using VideoJockey.Core.Entities;

namespace VideoJockey.Core.Specifications.DownloadQueue;

public sealed class DownloadQueueAllSpecification : BaseSpecification<DownloadQueueItem>
{
    public DownloadQueueAllSpecification()
    {
        ApplyCriteria(item => !item.IsDeleted);
        AddOrderByDescending(item => item.Priority);
        AddOrderBy(item => item.AddedDate);
    }
}
