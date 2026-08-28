# HW9 Video Community Domain Skill

## Global model

All operations occur in one `Network`. Official domain types are `NetworkInterface`,
`UserInterface`, and `VideoInterface`.

- A user has a globally unique ID, name, age, following users, followers, and received videos.
- A video has a globally unique ID and an uploader ID.
- User equality and video equality are defined by ID.
- `Network.users` and `Network.videos` contain no duplicate objects under their equality rules.

## User insertion

`addUser` succeeds only when the ID is absent and age is in `[0, 110]`. The new user starts with
empty following, followers, and received-video collections. Existing users remain present.

Exception priority:

1. duplicate ID → `EqualUserIdException`;
2. otherwise invalid age → `InvalidAgeException`.

## Upload and notification

`uploadVideo` requires an existing uploader and a new video ID. The video is inserted and every
current follower of the uploader receives the new video at the front of their queue; old queue
order is preserved.

## Following relation

Following is directed. A successful `followUser(id1, id2)` simultaneously establishes:

- user `id1` follows user `id2`;
- user `id2` contains user `id1` as a follower.

Exception priority:

1. `id1` missing;
2. otherwise `id2` missing;
3. otherwise self-follow;
4. otherwise duplicate following relation.

`unfollowUser` removes both directions of the same semantic relation atomically.

## Watching and received videos

Watching removes the specified video from that user's received-video collection. It does not
delete the global video or change social relations.

`queryReceivedUnwatchedVideos` returns at most the first five received video IDs in queue order.

## Queries

- `queryUpFollowersAgeRatio` returns four follower age ratios: `<=16`, `17..30`, `31..45`, `>=46`.
- `queryMutualFollowingSum` counts unordered user pairs that follow each other; each pair counts once.
- `queryShortestPath` follows directed `following` edges, returns zero for the same user, returns
  the minimum edge count for a reachable target, and throws `UncessException` if unreachable.
- Query methods must preserve observable network and nested-object state.

