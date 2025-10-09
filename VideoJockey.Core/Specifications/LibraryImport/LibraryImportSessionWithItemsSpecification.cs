using System;
using VideoJockey.Core.Entities;
using VideoJockey.Core.Specifications;

namespace VideoJockey.Core.Specifications.LibraryImport
{
    public class LibraryImportSessionWithItemsSpecification : BaseSpecification<LibraryImportSession>
    {
        public LibraryImportSessionWithItemsSpecification(Guid sessionId)
            : base(session => session.Id == sessionId)
        {
            AddInclude(session => session.Items);
        }
    }
}
