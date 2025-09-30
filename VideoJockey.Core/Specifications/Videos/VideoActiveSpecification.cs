using VideoJockey.Core.Entities;

namespace VideoJockey.Core.Specifications.Videos;

public sealed class VideoActiveSpecification : BaseSpecification<Video>
{
    public VideoActiveSpecification(bool includeRelations = false)
    {
        ApplyCriteria(v => v.IsActive);
        AddOrderBy(v => v.Title);

        if (includeRelations)
        {
            AddInclude(v => v.Genres);
            AddInclude(v => v.Tags);
            AddInclude(v => v.FeaturedArtists);
        }
    }
}
