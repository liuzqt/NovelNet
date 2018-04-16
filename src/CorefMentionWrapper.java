import edu.stanford.nlp.coref.data.CorefChain;

/**
 * Created by liuziqi on 2018/4/16.
 */
public class CorefMentionWrapper {
    CorefChain.CorefMention m;
    String string; //modified string

    public CorefMentionWrapper(CorefChain.CorefMention m, String string) {
        this.m = m;
        this.string = string;
    }
}
