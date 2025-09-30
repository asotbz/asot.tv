using System;
using System.Collections.Generic;
using System.Linq;
using VideoJockey.Core.Entities;

namespace VideoJockey.Core.Specifications.Lookups;

public sealed class GenreLookupSpecification : BaseSpecification<Genre>
{
    public GenreLookupSpecification(IEnumerable<Guid> genreIds)
    {
        if (genreIds == null)
        {
            throw new ArgumentNullException(nameof(genreIds));
        }

        var ids = genreIds.Distinct().ToList();
        if (ids.Count == 0)
        {
            ApplyCriteria(_ => false);
            return;
        }

        ApplyCriteria(genre => ids.Contains(genre.Id) && genre.IsActive);
        AddOrderBy(genre => genre.Name);
    }
}
