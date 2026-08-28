public interface NetworkInterface {
    /*@ public normal_behavior
      @ requires contains(userIds(), id1) && contains(userIds(), id2) && id1 != id2;
      @ assignable following(id1), followers(id2);
      @ ensures following(id1) == union(\old(following(id1)), singleton(id2));
      @ ensures followers(id2) == union(\old(followers(id2)), singleton(id1));
      @ ensures \forall int u; contains(userIds(), u) && u != id1; following(u) == \old(following(u));
      @ ensures \forall int u; contains(userIds(), u) && u != id2; followers(u) == \old(followers(u));
      @ ensures \forall int u; contains(userIds(), u); receivedVideos(u) == \old(receivedVideos(u));
      @*/
    void followUser(int id1, int id2);
}
