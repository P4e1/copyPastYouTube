from app.domain.videos import (
    VideoSnapshot,
    VideoStatus,
    View,
    Visibility,
    in_feed,
    view_access,
    visible_on_owner_channel,
)

OWNER = "owner-1"
VIEWER = "viewer-1"
GRANTEE = "grantee-1"


def _video(visibility: Visibility, status: VideoStatus, grants: frozenset[str] = frozenset()) -> VideoSnapshot:
    return VideoSnapshot(
        visibility=visibility,
        status=status,
        owner_id=OWNER,
        grant_user_ids=grants,
    )


def test_public_ready_is_visible_and_in_feed():
    video = _video(Visibility.public, VideoStatus.ready)

    assert view_access(video, VIEWER) is View.allowed
    assert in_feed(video) is True


def test_unlisted_opens_by_id_and_stays_out_of_feed():
    video = _video(Visibility.unlisted, VideoStatus.ready)

    assert view_access(video, VIEWER) is View.allowed
    assert in_feed(video) is False


def test_private_hides_stranger_and_shows_grant_and_owner():
    video = _video(Visibility.private, VideoStatus.ready, frozenset({GRANTEE}))

    assert view_access(video, VIEWER) is View.denied
    assert view_access(video, GRANTEE) is View.allowed
    assert view_access(video, OWNER) is View.allowed


def test_hidden_is_invisible_to_viewer_and_marked_for_owner():
    video = _video(Visibility.public, VideoStatus.hidden)

    assert view_access(video, VIEWER) is View.denied
    assert view_access(video, OWNER) is View.owner_marked
    assert in_feed(video) is False


def test_not_ready_stays_out_of_feed_and_on_owner_channel():
    for status in (VideoStatus.uploading, VideoStatus.processing, VideoStatus.failed):
        video = _video(Visibility.public, status)

        assert in_feed(video) is False
        assert visible_on_owner_channel(video, OWNER) is True
        assert visible_on_owner_channel(video, VIEWER) is False
        assert view_access(video, VIEWER) is View.denied
        assert view_access(video, OWNER) is View.owner_marked
