using System;
using Microsoft.AspNetCore.DataProtection;
using Microsoft.AspNetCore.Identity;
using Microsoft.EntityFrameworkCore;
using VideoJockey.Web.Hubs;
using MudBlazor.Services;
using Serilog;
using Serilog.Events;
using VideoJockey.Core.Entities;
using VideoJockey.Web.Identity;
using VideoJockey.Web.Middleware;
using VideoJockey.Web.Security;
using VideoJockey.Core.Interfaces;
using VideoJockey.Data.Context;
using VideoJockey.Data.Repositories;
using VideoJockey.Services;
using VideoJockey.Services.Interfaces;
using VideoJockey.Services.Models;

// Configure Serilog
Log.Logger = new LoggerConfiguration()
    .MinimumLevel.Debug()
    .MinimumLevel.Override("Microsoft", LogEventLevel.Information)
    .MinimumLevel.Override("Microsoft.AspNetCore", LogEventLevel.Warning)
    .MinimumLevel.Override("Microsoft.EntityFrameworkCore", LogEventLevel.Warning)
    .Enrich.FromLogContext()
    .WriteTo.Console(
        outputTemplate: "[{Timestamp:HH:mm:ss} {Level:u3}] {Message:lj}{NewLine}{Exception}")
    .WriteTo.File(
        "logs/videojockey-.txt",
        rollingInterval: RollingInterval.Day,
        rollOnFileSizeLimit: true,
        fileSizeLimitBytes: 10485760, // 10MB
        retainedFileCountLimit: 30,
        outputTemplate: "[{Timestamp:yyyy-MM-dd HH:mm:ss.fff zzz}] [{Level:u3}] {Message:lj}{NewLine}{Exception}")
    .CreateLogger();

try
{
    Log.Information("Starting VideoJockey application");

    var builder = WebApplication.CreateBuilder(args);

    // Add Serilog
    builder.Host.UseSerilog();

    // Add services to the container
    builder.Services.AddRazorComponents()
        .AddInteractiveServerComponents();

    // Add MudBlazor services
    builder.Services.AddMudServices();

    // SignalR for real-time updates
    builder.Services.AddSignalR();

    // Configure SQLite with Entity Framework Core
    var dataDirectory = Path.Combine(builder.Environment.ContentRootPath, "data");
    Directory.CreateDirectory(dataDirectory);
    var connectionString = $"Data Source={Path.Combine(dataDirectory, "videojockey.db")}";

    builder.Services.AddDbContext<ApplicationDbContext>(options =>
    {
        options.UseSqlite(connectionString);
        options.EnableSensitiveDataLogging(builder.Environment.IsDevelopment());
        options.EnableDetailedErrors(builder.Environment.IsDevelopment());
    });

    // Configure Data Protection for encryption
    var keysDirectory = Path.Combine(dataDirectory, "keys");
    Directory.CreateDirectory(keysDirectory);
    builder.Services.AddDataProtection()
        .PersistKeysToFileSystem(new DirectoryInfo(keysDirectory))
        .SetApplicationName("VideoJockey");

    builder.Services.AddAntiforgery(options =>
    {
        options.Cookie.Name = AntiforgeryDefaults.CookieName;
        options.Cookie.HttpOnly = true;
        options.Cookie.SameSite = SameSiteMode.Strict;
        options.Cookie.SecurePolicy = CookieSecurePolicy.SameAsRequest;
        options.HeaderName = AntiforgeryDefaults.HeaderName;
    });

    var identityCoreBuilder = builder.Services.AddIdentityCore<ApplicationUser>(options =>
    {
        options.Password.RequireDigit = false;
        options.Password.RequireNonAlphanumeric = false;
        options.Password.RequireUppercase = false;
        options.Password.RequiredLength = 8;
        options.User.RequireUniqueEmail = true;
        options.Lockout.MaxFailedAccessAttempts = 5;
        options.Lockout.DefaultLockoutTimeSpan = TimeSpan.FromMinutes(5);
    });

    identityCoreBuilder = identityCoreBuilder.AddRoles<IdentityRole<Guid>>();
    identityCoreBuilder.AddEntityFrameworkStores<ApplicationDbContext>();
    identityCoreBuilder.AddSignInManager();
    identityCoreBuilder.AddDefaultTokenProviders();

    builder.Services.AddScoped<IUserClaimsPrincipalFactory<ApplicationUser>, ApplicationUserClaimsPrincipalFactory>();

    builder.Services.AddAuthentication(options =>
    {
        options.DefaultScheme = IdentityConstants.ApplicationScheme;
        options.DefaultAuthenticateScheme = IdentityConstants.ApplicationScheme;
        options.DefaultChallengeScheme = IdentityConstants.ApplicationScheme;
    })
    .AddCookie(IdentityConstants.ApplicationScheme, options =>
    {
        options.LoginPath = "/auth/login";
        options.LogoutPath = "/auth/logout";
        options.AccessDeniedPath = "/auth/access-denied";
        options.SlidingExpiration = true;
        options.ExpireTimeSpan = TimeSpan.FromDays(14);
    });

    builder.Services.AddAuthorizationBuilder()
        .AddPolicy("ActiveUser", policy => policy.RequireAuthenticatedUser())
        .AddPolicy("AdminOnly", policy => policy.RequireRole("Admin"));


    // Register repositories and Unit of Work
    builder.Services.AddScoped(typeof(IRepository<>), typeof(Repository<>));
    builder.Services.AddScoped<IUnitOfWork, UnitOfWork>();
    builder.Services.AddScoped<IActivityLogRepository, ActivityLogRepository>();

    // Shared services
    builder.Services.AddSingleton<IDownloadTaskQueue, DownloadTaskQueue>();
    builder.Services.AddSingleton<IDownloadSettingsProvider, DownloadSettingsProvider>();

    // Register Services
    builder.Services.AddScoped<IYtDlpService, YtDlpService>();
    builder.Services.AddScoped<VideoJockey.Services.Interfaces.IDownloadQueueService, DownloadQueueService>();
    builder.Services.AddScoped<ILibraryPathManager, LibraryPathManager>();
    builder.Services.AddScoped<IFileOrganizationService, FileOrganizationService>();
    builder.Services.AddScoped<IMetadataService, MetadataService>();
    builder.Services.AddScoped<IMetadataExportService, MetadataExportService>();
    builder.Services.AddScoped<VideoJockey.Services.Interfaces.ICollectionService, VideoJockey.Services.CollectionService>();
    builder.Services.AddScoped<IBulkOrganizeService, BulkOrganizeService>();
    builder.Services.AddScoped<INfoExportService, NfoExportService>();
    builder.Services.AddScoped<IVideoService, VideoService>();
    builder.Services.AddScoped<ISearchService, SearchService>();
    builder.Services.AddScoped<IExternalSearchService, ExternalSearchService>();
    builder.Services.AddScoped<IThumbnailService, ThumbnailService>();
    builder.Services.AddScoped<IPlaylistService, PlaylistService>();
    builder.Services.AddScoped<IActivityLogService, ActivityLogService>();
    builder.Services.AddScoped<ILibraryImportService, LibraryImportService>();
    builder.Services.AddScoped<ISourceVerificationService, SourceVerificationService>();
    builder.Services.AddSingleton<IVideoUpdateNotifier, VideoJockey.Web.Services.SignalRVideoUpdateNotifier>();
    builder.Services.AddScoped<IBackupService, BackupService>();
    
    // Add HttpContextAccessor for ActivityLogService
    builder.Services.AddHttpContextAccessor();
    
    // Register Background Services
    builder.Services.AddHostedService<DownloadBackgroundService>();
    builder.Services.AddHostedService<ThumbnailBackgroundService>();

    // Add health checks
    builder.Services.AddHealthChecks()
        .AddDbContextCheck<ApplicationDbContext>("database");

    // Add HttpClient for external API calls
    builder.Services.AddHttpClient();

    // Add memory cache
    builder.Services.AddMemoryCache();

    builder.Services.AddOptions<ImvdbOptions>()
        .Bind(builder.Configuration.GetSection("Imvdb"))
        .Configure(options =>
        {
            options.ApiKey ??= builder.Configuration["ApiKeys:ImvdbApiKey"];
        });

    builder.Services.AddImvdbIntegration();
    
    // Add web-specific services
    builder.Services.AddScoped<VideoJockey.Web.Services.KeyboardShortcutService>();

    // Configure CORS (if needed for API access)
    builder.Services.AddCors(options =>
    {
        options.AddPolicy("AllowAll", policy =>
        {
            policy.AllowAnyOrigin()
                  .AllowAnyMethod()
                  .AllowAnyHeader();
        });
    });

    var app = builder.Build();

    // Configure the HTTP request pipeline
    if (!app.Environment.IsDevelopment())
    {
        app.UseExceptionHandler("/Error", createScopeForErrors: true);
        // The default HSTS value is 30 days
        app.UseHsts();
    }

    // Use Serilog request logging
    app.UseSerilogRequestLogging(options =>
    {
        options.MessageTemplate = "HTTP {RequestMethod} {RequestPath} responded {StatusCode} in {Elapsed:0.0000} ms";
        options.GetLevel = (httpContext, elapsed, ex) => LogEventLevel.Debug;
        options.EnrichDiagnosticContext = (diagnosticContext, httpContext) =>
        {
            diagnosticContext.Set("RequestHost", httpContext.Request.Host.Value ?? "unknown");
            diagnosticContext.Set("RequestScheme", httpContext.Request.Scheme);
        };
    });

    app.UseHttpsRedirection();
    app.UseStaticFiles();
    app.UseMiddleware<AntiforgeryCookieCleanupMiddleware>();
    app.UseAntiforgery();

    app.UseAuthentication();
    app.UseAuthorization();
    
    // Use setup check middleware to redirect to setup if not configured
    app.UseSetupCheck();

    // Map health check endpoints
    app.MapHealthChecks("/health");
    app.MapHealthChecks("/health/ready", new Microsoft.AspNetCore.Diagnostics.HealthChecks.HealthCheckOptions
    {
        Predicate = check => check.Tags.Contains("ready")
    });
    app.MapHealthChecks("/health/live", new Microsoft.AspNetCore.Diagnostics.HealthChecks.HealthCheckOptions
    {
        Predicate = _ => false
    });

    app.MapRazorComponents<VideoJockey.Web.Components.App>()
        .AddInteractiveServerRenderMode();

    app.MapHub<VideoUpdatesHub>("/hubs/updates");

    app.MapGet("/auth/setup-complete", async (
        HttpContext httpContext,
        string? token,
        SignInManager<ApplicationUser> signInManager,
        IUnitOfWork unitOfWork,
        ILogger<Program> logger) =>
    {
        if (string.IsNullOrWhiteSpace(token))
        {
            logger.LogWarning("Setup sign-in attempted without a token.");
            return Results.Redirect("/auth/login");
        }

        var storedTokenConfig = await unitOfWork.Configurations
            .FirstOrDefaultAsync(c => c.Key == "SetupSignInToken" && c.Category == "System" && c.IsActive);

        if (storedTokenConfig?.Value is null)
        {
            logger.LogWarning("Setup sign-in token not found or already used.");
            return Results.Redirect("/auth/login");
        }

        var tokenParts = storedTokenConfig.Value.Split('|', 2, StringSplitOptions.TrimEntries);
        if (tokenParts.Length != 2 || !string.Equals(tokenParts[0], token, StringComparison.Ordinal))
        {
            logger.LogWarning("Setup sign-in token mismatch.");
            return Results.Redirect("/auth/login");
        }

        var userId = tokenParts[1];
        var user = await signInManager.UserManager.FindByIdAsync(userId);
        if (user is null)
        {
            logger.LogWarning("Setup sign-in user not found for token.");
            return Results.Redirect("/auth/login");
        }

        user.LockoutEnabled = false;
        user.LockoutEnd = null;
        await signInManager.UserManager.UpdateAsync(user);
        await signInManager.UserManager.ResetAccessFailedCountAsync(user);

        await signInManager.SignInAsync(user, isPersistent: true);
        logger.LogInformation("Administrator {AdminEmail} signed in via setup completion endpoint.", user.Email);

        storedTokenConfig.IsActive = false;
        storedTokenConfig.Value = string.Empty;
        await unitOfWork.Configurations.UpdateAsync(storedTokenConfig);
        await unitOfWork.SaveChangesAsync();

        return Results.Redirect("/dashboard");
    }).AllowAnonymous();

    // Apply database migrations and check first run
    using (var scope = app.Services.CreateScope())
    {
        var dbContext = scope.ServiceProvider.GetRequiredService<ApplicationDbContext>();
        var logger = scope.ServiceProvider.GetRequiredService<ILogger<Program>>();

        try
        {
            logger.LogInformation("Applying database migrations...");
            dbContext.Database.Migrate();
            logger.LogInformation("Database migrations applied successfully");

            // Check if this is the first run
            var unitOfWork = scope.ServiceProvider.GetRequiredService<IUnitOfWork>();
            var firstRunConfig = await unitOfWork.Configurations
                .FirstOrDefaultAsync(c => c.Key == "IsFirstRun" && c.Category == "System");

            if (firstRunConfig != null && firstRunConfig.Value == "true")
            {
                logger.LogInformation("First run detected - setup wizard will be shown");
            }
        }
        catch (Exception ex)
        {
            logger.LogError(ex, "An error occurred while migrating the database");
            throw;
        }
    }

    Log.Information("VideoJockey application started successfully");
    app.Run();
}
catch (Exception ex)
{
    Log.Fatal(ex, "VideoJockey application terminated unexpectedly");
}
finally
{
    Log.CloseAndFlush();
}

// Make the implicit Program class public so test projects can access it
public partial class Program { }
