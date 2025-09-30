using VideoJockey.Core.Entities;
using VideoJockey.Core.Interfaces;
using VideoJockey.Core.Specifications;
using VideoJockey.Core.Specifications.Queries;
using VideoJockey.Core.Specifications.Videos;
using VideoJockey.Services.Interfaces;

namespace VideoJockey.Services;

public class VideoService : IVideoService
{
    private readonly IRepository<Video> _videoRepository;
    private readonly IUnitOfWork _unitOfWork;

    public VideoService(IRepository<Video> videoRepository, IUnitOfWork unitOfWork)
    {
        _videoRepository = videoRepository;
        _unitOfWork = unitOfWork;
    }

    public async Task<List<Video>> GetAllVideosAsync(CancellationToken cancellationToken = default)
    {
        var results = new List<Video>();
        var query = new VideoQuery
        {
            Page = 1,
            PageSize = 200,
            SortBy = VideoSortOption.Title,
            SortDirection = SortDirection.Ascending
        };

        while (true)
        {
            var specification = new VideoQuerySpecification(
                query,
                includeGenres: true,
                includeTags: true,
                includeFeaturedArtists: true,
                includeCollections: true);

            var page = await _videoRepository.ListAsync(specification);
            results.AddRange(page);

            if (page.Count < query.PageSize)
            {
                break;
            }

            query.Page += 1;
        }

        return results;
    }

    public async Task<Video?> GetVideoByIdAsync(Guid id, CancellationToken cancellationToken = default)
    {
        var specification = new VideoByIdSpecification(id);
        return await _videoRepository.FirstOrDefaultAsync(specification);
    }

    public async Task<Video> CreateVideoAsync(Video video, CancellationToken cancellationToken = default)
    {
        await _videoRepository.AddAsync(video);
        await _unitOfWork.SaveChangesAsync();
        return video;
    }

    public async Task<Video> UpdateVideoAsync(Video video, CancellationToken cancellationToken = default)
    {
        await _videoRepository.UpdateAsync(video);
        await _unitOfWork.SaveChangesAsync();
        return video;
    }

    public async Task DeleteVideoAsync(Guid id, CancellationToken cancellationToken = default)
    {
        var video = await _videoRepository.GetByIdAsync(id);
        if (video != null)
        {
            await _videoRepository.DeleteAsync(video);
            await _unitOfWork.SaveChangesAsync();
        }
    }

    public async Task<List<Video>> GetVideosByArtistAsync(string artist, CancellationToken cancellationToken = default)
    {
        var specification = new VideosByArtistSpecification(artist);
        var results = await _videoRepository.ListAsync(specification);
        return new List<Video>(results);
    }

    public async Task<List<Video>> GetVideosByGenreAsync(Guid genreId, CancellationToken cancellationToken = default)
    {
        var specification = new VideosByGenreSpecification(genreId);
        var results = await _videoRepository.ListAsync(specification);
        return new List<Video>(results);
    }

    public async Task<List<Video>> GetRecentVideosAsync(int count = 10, CancellationToken cancellationToken = default)
    {
        var specification = new VideoRecentImportsSpecification(count);
        var results = await _videoRepository.ListAsync(specification);
        return new List<Video>(results);
    }

    public async Task<PagedResult<Video>> GetVideosAsync(VideoQuery query, CancellationToken cancellationToken = default)
    {
        if (query == null)
        {
            throw new ArgumentNullException(nameof(query));
        }

        var listingSpecification = new VideoQuerySpecification(
            query,
            includeGenres: true,
            includeTags: true,
            includeFeaturedArtists: true,
            includeCollections: false,
            applyPaging: true);

        var countSpecification = new VideoQuerySpecification(
            query,
            includeGenres: false,
            includeTags: false,
            includeFeaturedArtists: false,
            includeCollections: false,
            applyPaging: false);

        var items = await _videoRepository.ListAsync(listingSpecification);
        var total = await _videoRepository.CountAsync(countSpecification);

        return new PagedResult<Video>(items, total, query.Page, query.PageSize);
    }
}
