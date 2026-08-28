# HW9 Specification Agent — Analyzer Stage

---

## Stage instructions

# Role

You are the Requirement Analyzer of an HW9 specification-design agent.

Convert natural-language requirements into semantic YAML. Do not generate JML and do not design
Java data structures.

# Inputs

- original requirement;
- official interface context;
- HW9 Domain Skill.

# Output schema

```yaml
method:
behavior_type: pure_query | mutation | mixed_or_unclear
parameters: []
entities_read: []
normal_conditions: []
derived_values: []
state_changes: []
conditional_state_changes: []
unchanged_state: []
return_constraints: []
exceptions:
  - name:
    condition:
    priority:
atomicity_requirements: []
ordering: []
scope_constraints: []
missing_information: []
ambiguities: []
unsupported_assumptions: []
```

# Rules

Do not invent interface members. Preserve exception priority. Separate semantic state from Java
representation. Put unresolved facts in `missing_information` or `ambiguities`.



---

## Skill: hw9_domain.md

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



---

## Original requirement

# followUser 自然语言需求

在全局 Network 中执行 `followUser(id1, id2)`。

成功关注必须同时满足：用户 `id1` 存在、用户 `id2` 存在、二者不是同一用户，且
`id1` 当前没有关注 `id2`。成功后，`id1` 的关注列表包含 `id2`，同时 `id2` 的
粉丝列表包含 `id1`，并输出 `follow_user succeeded`。除这两个方向的关系变化外，
其他用户、视频、接收视频队列以及用户基本属性均不得改变。

异常按照以下优先级处理：

1. `id1` 不存在时抛出 `UserIdNotFoundException`；
2. `id1` 存在但 `id2` 不存在时抛出 `UserIdNotFoundException`；
3. 两个用户都存在但 `id1 == id2` 时抛出 `SelfSubscriptionException`；
4. 两个用户都存在、ID 不同但关注关系已经存在时抛出 `DuplicateSubscriptionException`。

任何异常分支均不得建立部分关注关系或产生其他业务状态修改。



---

## Official interface grounding

```json
{
  "interface": "NetworkInterface",
  "name": "followUser",
  "signature": "void followUser(int id1, int id2) throws UserIdNotFoundException, SelfSubscriptionException, DuplicateSubscriptionException",
  "jml": "public normal_behavior\nrequires containsUser(id1) && containsUser(id2) && id1 != id2 && !getUser(id1).isFollowing(getUser(id2));\nassignable users[*];\nensures getUser(id1).isFollowing(getUser(id2));\nensures getUser(id2).containsFollower(getUser(id1));\nensures (* output-> \"follow_user succeeded\" *);\nalso\npublic exceptional_behavior\nsignals (UserIdNotFoundException e) !containsUser(id1);\nsignals (UserIdNotFoundException e) containsUser(id1) && !containsUser(id2);\nsignals (SelfSubscriptionException e) containsUser(id1) && containsUser(id2) && id1 == id2;\nsignals (DuplicateSubscriptionException e) containsUser(id1) && containsUser(id2) && id1 != id2 && getUser(id1).isFollowing(getUser(id2));",
  "markers": [
    "safe"
  ],
  "requires": [
    "containsUser(id1) && containsUser(id2) && id1 != id2 && !getUser(id1).isFollowing(getUser(id2))"
  ],
  "assignable": [
    "users[*]"
  ],
  "ensures": [
    "getUser(id1).isFollowing(getUser(id2))",
    "getUser(id2).containsFollower(getUser(id1))",
    "(* output-> \"follow_user succeeded\" *)"
  ],
  "signals": [
    "(UserIdNotFoundException e) !containsUser(id1)",
    "(UserIdNotFoundException e) containsUser(id1) && !containsUser(id2)",
    "(SelfSubscriptionException e) containsUser(id1) && containsUser(id2) && id1 == id2",
    "(DuplicateSubscriptionException e) containsUser(id1) && containsUser(id2) && id1 != id2 && getUser(id1).isFollowing(getUser(id2))"
  ],
  "behavior_kinds": [
    "normal_behavior",
    "exceptional_behavior"
  ]
}
```

---

## Your response

Return only the output required by the stage instructions.
