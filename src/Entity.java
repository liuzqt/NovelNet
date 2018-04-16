import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Set;

/**
 * Created by liuziqi on 2018/4/16.
 */
public class Entity {
    public int id;
    public Set<String> names;
    public int frequency;
    public HashMap<Entity, Integer> neighborInteract;

    public Entity(int id) {
        this.id = id;
        this.names = new HashSet<>();
        this.frequency = 0;
        neighborInteract = new HashMap<>();
    }

    public String toString() {
        return Arrays.toString(names.toArray());
    }

}
