public interface NetworkInterface {
    /*@ public normal_behavior
      @ requires contains(userIds(), id1) && contains(userIds(), id2) && id1 != id2;
      @ assignable following(id1), followers(id2);
      @ ensures contains(following(id1), id2);
      @ ensures contains(followers(id2), id1);
      @*/
    void followUser(int id1, int id2);
}
