using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using VideoJockey.Core.Entities;
using VideoJockey.Core.Interfaces;
using VideoJockey.Core.Specifications;
using VideoJockey.Core.Specifications.Queries;
using VideoJockey.Core.Specifications.Videos;
using VideoJockey.Data.Context;
using SearchContracts = VideoJockey.Services.Interfaces;

namespace VideoJockey.Services
{
public class SearchService : SearchContracts.ISearchService
{
        private readonly ApplicationDbContext _context;
        private readonly IUnitOfWork _unitOfWork;
    private readonly ILogger<SearchService> _logger;

    public SearchService(ApplicationDbContext context, IUnitOfWork unitOfWork, ILogger<SearchService> logger)
        {
            _context = context;
            _unitOfWork = unitOfWork;
            _logger = logger;
        }

    public async Task<SearchContracts.SearchResult> SearchAsync(SearchContracts.SearchQuery query)
        {
            var videoQuery = BuildVideoQuery(query);

            var listingSpecification = new VideoQuerySpecification(
                videoQuery,
                includeGenres: true,
                includeTags: true,
                includeFeaturedArtists: true,
                includeCollections: true,
                applyPaging: true);

            var countSpecification = new VideoQuerySpecification(
                videoQuery,
                includeGenres: false,
                includeTags: false,
                includeFeaturedArtists: false,
                includeCollections: false,
                applyPaging: false);

            var videos = await _unitOfWork.Videos.ListAsync(listingSpecification);
            var totalCount = await _unitOfWork.Videos.CountAsync(countSpecification);

            IReadOnlyList<Video> facetSource;
            if (totalCount <= videoQuery.PageSize)
            {
                facetSource = videos;
            }
            else
            {
                var facetSpecification = new VideoQuerySpecification(
                    videoQuery,
                    includeGenres: true,
                    includeTags: false,
                    includeFeaturedArtists: false,
                    includeCollections: true,
                    applyPaging: false);

                facetSource = await _unitOfWork.Videos.ListAsync(facetSpecification);
            }

        var facets = GenerateFacets(facetSource);

        return new SearchContracts.SearchResult
        {
            Videos = videos.ToList(),
            TotalCount = totalCount,
            PageNumber = videoQuery.Page,
            PageSize = videoQuery.PageSize,
                Facets = facets
            };
        }

    private static VideoQuery BuildVideoQuery(SearchContracts.SearchQuery query)
        {
            var videoQuery = new VideoQuery
            {
                Search = query.SearchText,
                Page = query.PageNumber,
                PageSize = query.PageSize,
                SortBy = MapSortOption(query.SortBy),
                SortDirection = query.SortDescending ? SortDirection.Descending : SortDirection.Ascending,
                YearFrom = query.YearFrom,
                YearTo = query.YearTo,
                DurationFrom = query.DurationMin,
                DurationTo = query.DurationMax,
                HasCollections = query.HasCollections,
                HasYouTubeId = query.HasYouTubeId,
                HasImvdbId = query.HasImvdbId,
                AddedAfter = query.AddedAfter,
                AddedBefore = query.AddedBefore
            };

            videoQuery.ArtistNames.AddRange(query.Artists);
            videoQuery.GenreNames.AddRange(query.Genres);
            videoQuery.Formats.AddRange(query.Formats);
            videoQuery.Resolutions.AddRange(query.Resolutions);

            if (query.CollectionIds.Any())
            {
                videoQuery.CollectionIds.AddRange(query.CollectionIds);
            }

            return videoQuery;
        }

        private static VideoSortOption MapSortOption(string? sortBy)
        {
            return sortBy?.ToLowerInvariant() switch
            {
                "artist" => VideoSortOption.Artist,
                "year" => VideoSortOption.Year,
                "duration" => VideoSortOption.Duration,
                "created" => VideoSortOption.CreatedAt,
                "modified" => VideoSortOption.UpdatedAt,
                _ => VideoSortOption.Title
            };
        }

        private static SearchContracts.SearchFacets GenerateFacets(IEnumerable<Video> videos)
        {
            var facets = new SearchContracts.SearchFacets();

            var videoList = videos.ToList();

            facets.Artists = videoList
                .Where(v => !string.IsNullOrWhiteSpace(v.Artist))
                .GroupBy(v => v.Artist!)
                .ToDictionary(g => g.Key, g => g.Count(), StringComparer.OrdinalIgnoreCase);

            facets.Genres = videoList
                .SelectMany(v => v.Genres ?? Enumerable.Empty<Genre>())
                .Where(g => !string.IsNullOrWhiteSpace(g.Name))
                .GroupBy(g => g.Name)
                .ToDictionary(g => g.Key, g => g.Count(), StringComparer.OrdinalIgnoreCase);

            facets.Formats = videoList
                .Where(v => !string.IsNullOrWhiteSpace(v.Format))
                .GroupBy(v => v.Format!)
                .ToDictionary(g => g.Key, g => g.Count(), StringComparer.OrdinalIgnoreCase);

            facets.Resolutions = videoList
                .Where(v => !string.IsNullOrWhiteSpace(v.Resolution))
                .GroupBy(v => v.Resolution!)
                .ToDictionary(g => g.Key, g => g.Count(), StringComparer.OrdinalIgnoreCase);

            facets.Years = videoList
                .Where(v => v.Year.HasValue)
                .GroupBy(v => v.Year!.Value.ToString())
                .ToDictionary(g => g.Key, g => g.Count());

            facets.Collections = videoList
                .SelectMany(v => v.CollectionVideos ?? Enumerable.Empty<CollectionVideo>())
                .Where(cv => cv.Collection != null && !string.IsNullOrWhiteSpace(cv.Collection.Name))
                .GroupBy(cv => cv.Collection!.Name)
                .ToDictionary(g => g.Key, g => g.Count(), StringComparer.OrdinalIgnoreCase);

            return facets;
        }

        public async Task<List<SavedSearch>> GetSavedSearchesAsync()
        {
            return await _context.Set<SavedSearch>()
                .Where(s => s.IsActive)
                .OrderBy(s => s.Name)
                .ToListAsync();
        }

        public async Task<SavedSearch> GetSavedSearchAsync(Guid id)
        {
            var search = await _context.Set<SavedSearch>()
                .FirstOrDefaultAsync(s => s.Id == id && s.IsActive);

            if (search == null)
                throw new KeyNotFoundException($"Saved search with ID {id} not found");

            return search;
        }

        public async Task<SavedSearch> SaveSearchAsync(SavedSearch savedSearch)
        {
            if (savedSearch.Id == Guid.Empty)
            {
                savedSearch.Id = Guid.NewGuid();
                savedSearch.CreatedAt = DateTime.UtcNow;
                _context.Set<SavedSearch>().Add(savedSearch);
            }
            else
            {
                savedSearch.UpdatedAt = DateTime.UtcNow;
                _context.Set<SavedSearch>().Update(savedSearch);
            }

            await _context.SaveChangesAsync();
            return savedSearch;
        }

        public async Task DeleteSavedSearchAsync(Guid id)
        {
            var search = await GetSavedSearchAsync(id);
            search.IsActive = false;
            search.UpdatedAt = DateTime.UtcNow;
            _context.Set<SavedSearch>().Update(search);
            await _context.SaveChangesAsync();
        }

        public async Task<SearchContracts.SearchFacets> GetSearchFacetsAsync()
        {
            var allVideos = await _unitOfWork.Videos.ListAsync(new VideoActiveSpecification(includeRelations: true));
            return GenerateFacets(allVideos);
        }
    }
}
