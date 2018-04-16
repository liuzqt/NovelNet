import edu.stanford.nlp.pipeline.StanfordCoreNLP;

import java.util.Properties;

public class test {
    public static void main(String[] args) throws Exception {
//        String text = new String(Files.readAllBytes(Paths.get("./test.txt")));


        String text = "Harry Dummy Potter study in Dragon Planet. Potter has a dog called Bobby and he loves it. He loves Maggie and he is Maggie's father.";

        Properties props = new Properties();
        props.setProperty("annotators", "tokenize,ssplit,pos,lemma,ner, parse,coref");
        props.setProperty("coref.algorithm", "statistical");
        StanfordCoreNLP pipeline = new StanfordCoreNLP(props);
        Relationship relationship = new Relationship(pipeline, text, "", 20, true);
        System.out.println(relationship.report());


//
//        CoreDocument document = new CoreDocument(text);
//        pipeline.annotate(document);
//        System.out.println("---");
//        System.out.println("coref chains");
//
//        for (CorefChain cc : document.corefChains().values()) {
//            System.out.println("++++++++++++++++++++++++++++++");
//            System.out.println("chain ID "+cc.getChainID());
//            System.out.println(cc);
//
//            for (CorefChain.CorefMention m : cc.getMentionsInTextualOrder()) {
//                System.out.println();
//                System.out.println("mentionID " + m.mentionID);
//                System.out.println(m.toString());
//                System.out.println("cluster ID " + m.corefClusterID);
//                System.out.println("headIdx " + m.headIndex);
//                System.out.println("endIdx " + m.endIndex);
//                System.out.println("mentionSpan " + m.mentionSpan);
//                System.out.println("startIdx " + m.startIndex);
//                System.out.println("position " + m.position);
//                System.out.println("sen num " + m.sentNum);
//
//            }
//        }
//        for (CoreSentence sentence : document.sentences()) {
//
//            System.out.println("sentence.......................");
//            System.out.println();
//            for (CoreLabel s : sentence.tokens()) {
//                System.out.printf("%s\t%s\t%d\t%d\n",s.originalText(),s.ner(),s.beginPosition(),s.endPosition());
//            }
//
//        }
    }
}
