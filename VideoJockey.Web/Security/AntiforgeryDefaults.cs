using Microsoft.AspNetCore.Antiforgery;

namespace VideoJockey.Web.Security
{
    /// <summary>
    /// Shared antiforgery configuration values so cookie names stay consistent.
    /// </summary>
    public static class AntiforgeryDefaults
    {
        public const string CookieName = "vj-antiforgery";

        public const string HeaderName = "X-CSRF-TOKEN";
    }
}
