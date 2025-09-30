using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using static VideoJockey.Services.BulkOrganizeService;

namespace VideoJockey.Services.Interfaces
{
    public interface IBulkOrganizeService
    {
        /// <summary>
        /// Organize multiple videos based on the specified pattern and options
        /// </summary>
        Task<OrganizeResult> OrganizeVideosAsync(
            IEnumerable<Guid> videoIds, 
            OrganizeOptions options);
        
        /// <summary>
        /// Preview the organization results without making changes
        /// </summary>
        Task<Dictionary<string, int>> PreviewOrganizeAsync(
            IEnumerable<Guid> videoIds,
            OrganizeOptions options);
        
        /// <summary>
        /// Get list of available variables for patterns
        /// </summary>
        List<string> GetAvailableVariables();
        
        /// <summary>
        /// Get sample organization patterns
        /// </summary>
        List<string> GetSamplePatterns();
    }
}