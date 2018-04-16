/**
 * Created by liuziqi on 2018/4/16.
 */
public class MentionToken {
    public int mentionID;
    public int absPos;
    public int senNum;
    public int clusterID;
    public String name;
    public Entity entity;

    public MentionToken(int mentionID, int absPos, int senNum, int clusterID, String name, Entity entity) {
        this.mentionID = mentionID;
        this.absPos = absPos;
        this.senNum = senNum;
        this.clusterID = clusterID;
        this.name = name;
        this.entity = entity;
    }
}
