import categen


def submit(username: str, eid: int, hid: int, desc: str = ""):
    catentry = categen.CatalogueEntry(eid=eid, hid=hid, desc=desc)
    catentry.submission = f"Community Submission by {username}"
    catentry.rating = "100% Upvotes"
