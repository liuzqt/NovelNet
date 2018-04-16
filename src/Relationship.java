import edu.stanford.nlp.coref.data.CorefChain;
import edu.stanford.nlp.ling.CoreLabel;
import edu.stanford.nlp.pipeline.CoreDocument;
import edu.stanford.nlp.pipeline.CoreSentence;
import edu.stanford.nlp.pipeline.StanfordCoreNLP;

import java.util.*;
import java.util.stream.Collectors;
import java.util.stream.Stream;

/**
 * Created by liuziqi on 2018/4/15.
 */
public class Relationship {
    private final Set<String> pronoun = Stream.of("he", "she", "it", "him", "her", "they", "them").collect(Collectors.toSet());

    private final String PERSON = "PERSON"; // NER tag, can also add ORGANIZATION if needed
    private int entityCount; // total entity, also as an increasing ID, but notice that some entities might be merged, causing the missing id
    private int mergeCount;
    private int threshold;  // how many words allowed between two entities that they can be recognized as relationship
    StanfordCoreNLP pipeline;
    private boolean debug;
    ArrayList<String> sections;  // split the whole text into sections according to different granularity
    HashMap<String, Entity> entityNameMap; // the same entity might have different names
    HashSet<Entity> entitySet;


    public Relationship(StanfordCoreNLP pipeline, String text, String granularity, int threshold, boolean debug) {
        this.debug = debug;
        this.entityCount = 0;
        this.mergeCount = 0;
        this.threshold = threshold;
        this.pipeline = pipeline;
        this.entityNameMap = new HashMap<>();
        this.entitySet = new HashSet<>();
        sections = getSections(text, granularity);
        if (debug) {
            System.out.println("document divided into " + this.sections.size() + " sections");
        }

        for (int i = 0; i < sections.size(); i++) {
            // for each section
            String section = sections.get(i);
            if (debug)
                System.out.println("processing section " + i);
            List<MentionToken> tokens = this.parseCoref(section);
            parseRelationship(tokens);
        }
    }

    private ArrayList<String> getSections(String text, String granularity) {
        return Arrays.stream(text.trim().split("\\n{2,}")).collect(Collectors.toCollection(ArrayList::new));
    }

    /**
     * @param tokens mention tokens from one section
     */
    private void parseRelationship(List<MentionToken> tokens) {
        System.out.println(Arrays.toString(entityNameMap.keySet().toArray()));
        // Noticed that the tokens appear in their text order
        // Noticed that all overlapping entities have already been merged here,
        // so overlapping entities won't interact with each other
        Queue<MentionToken> queue = new LinkedList<>();
        for (MentionToken m : tokens) {

            // remove those far away entity. (not in the same sentence and [threshold words] aways
            while (!queue.isEmpty() && m.absPos - queue.peek().absPos > threshold && queue.peek().senNum < m.senNum) {
                queue.poll();
            }


            for (Entity neighbor : queue.stream().map(o -> o.entity).distinct().collect(Collectors.toList())) {
                happenRelationship(m.entity, neighbor);
            }

            queue.offer(m);
        }
    }

    private void happenRelationship(Entity e1, Entity e2) {
        // 发生关系！
        if (!e1.equals(e2)) {
            e1.neighborInteract.put(e2, e1.neighborInteract.getOrDefault(e2, 0) + 1);
            e2.neighborInteract.put(e1, e2.neighborInteract.getOrDefault(e1, 0) + 1);
        }

    }


    /**
     * @param text original text from one section
     * @return list of mention token (sorted in their textual order)
     */
    private List<MentionToken> parseCoref(String text) {

        // a big problem is that coref annotator will skip those named entity which is not referred by a pronoun
        // for example "David is a boy" won't produce any result from coref annotator, while "David is a boy and he like swimming" will.
        // therefore, we should also use NER combined with Coref result

        // this is useful when parsing NER, to avoid duplicate entry from Coref, identified as absPos
        HashMap<Integer, MentionToken> tokenMap = new HashMap<>(); // key: absPos

        CoreDocument document = new CoreDocument(text);
        pipeline.annotate(document);

        if (debug) {
            System.out.println(document.corefChains().values().size() + " coref chains detected.");
            for (CorefChain cc : document.corefChains().values()) {
                System.out.println(cc);
            }
        }
        List<MentionToken> mentions = new ArrayList<>();

        // accumulated sum. the start index (in the whole text) of each sentence
        List<Integer> sentenceLen = Stream.of(0).collect(Collectors.toList());
        document.sentences().forEach(o -> sentenceLen.add(sentenceLen.get(sentenceLen.size() - 1) + o.tokens().size()));


        for (CorefChain corefChain : document.corefChains().values()) {
            List<CorefChain.CorefMention> cluster = corefChain.getMentionsInTextualOrder();
            Entity entity = getEntity(cluster);

            for (CorefChain.CorefMention m : cluster) {
                MentionToken token = new MentionToken(
                        m.mentionID,
                        m.startIndex + sentenceLen.get(m.sentNum - 1) - 1,
                        m.sentNum, m.corefClusterID,
                        m.mentionSpan.toLowerCase(),
                        entity);
                mentions.add(token);
                tokenMap.put(token.absPos, token);
            }
        }

        // parse NER here
        int maxClusterID = mentions.stream().map(o -> o.clusterID).max((o1, o2) -> o1 - o2).orElse(0);
        // we need to manually assign clusterID to those entity that doesn't appear in Coref
        List<CoreSentence> sentences = document.sentences();
        for (int i = 0; i < sentences.size(); i++) {
            // iterate over sentences
            CoreSentence sen = sentences.get(i);
            List<CoreLabel> tokens = sen.tokens();
            int startIdx = -1;
            boolean pre = false;
            for (int j = 0; j < tokens.size(); j++) {
                // iterate over tokens
                CoreLabel tk = tokens.get(j);
                if (tk.ner().equals(PERSON)) {
                    if (!pre) {
                        pre = true;
                        startIdx = j;
                    }
                    if (j == tokens.size() - 1) {
                        int endIdx = j;
                        int absPos = sentenceLen.get(i) + startIdx;
                        if (!tokenMap.containsKey(absPos))
                            extractNerEntity(startIdx, endIdx, text, tokens, mentions, i, absPos, ++maxClusterID);
                    }
                } else {
                    if (pre) {
                        pre = false;
                        int endIdx = j - 1;
                        int absPos = sentenceLen.get(i) + startIdx;
                        if (!tokenMap.containsKey(absPos))
                            extractNerEntity(startIdx, endIdx, text, tokens, mentions, i, absPos, ++maxClusterID);
                    }

                }
            }

        }

        // sorted by their order in the text
        mentions.sort((Comparator.comparingInt(o -> o.absPos)));
        if (debug) {
            for (MentionToken m : mentions) {
                System.out.println(m.name + " " + m.absPos);
            }
        }
        return mentions;
    }

    /**
     * a helper function called in parseCoref
     *
     * @param startIdx
     * @param endIdx
     * @param text
     * @param tokens
     * @param mentions
     * @param senNum
     * @param absPos
     * @param id
     */
    private void extractNerEntity(int startIdx, int endIdx, String text, List<CoreLabel> tokens, List<MentionToken> mentions, int senNum, int absPos, int id) {

        String name = text.substring(tokens.get(startIdx).beginPosition(), tokens.get(endIdx).endPosition()).toLowerCase();
        Entity entity = entityNameMap.getOrDefault(name, new Entity(entityCount++));
        entity.frequency++;
        entity.names.add(name);

        mentions.add(new MentionToken(-1, absPos, senNum, id, name, entity));
        entityNameMap.put(name, entity);
        entitySet.add(entity);
    }

    /**
     * @param cluster a coref cluster
     * @return identify the entity they refer to (if non-exist then create a new one)
     */
    private Entity getEntity(List<CorefChain.CorefMention> cluster) {
        int appearCount = cluster.size();
        List<String> cluster_names = cluster.stream()
                .map(o -> o.mentionSpan.toLowerCase())
                .distinct()
                .filter(o -> !pronoun.contains(o))
                .collect(Collectors.toList());

        // if all names are pronoun (but I suppose this situation will not happen
        if (cluster_names.isEmpty())
            return null;

        List<Entity> entities = cluster_names.stream()
                .map(o -> entityNameMap.getOrDefault(o, null))
                .distinct()
                .filter(Objects::nonNull)
                .collect(Collectors.toList());

        // if zero entity, which mean this entity hans't appear before
        // one entity, that's the best case
        // more than one entity, we merge those entities here
        Entity entity = null;
        switch (entities.size()) {
            case 0:
                entity = new Entity(entityCount++);
                break;
            case 1:
                entity = entities.get(0);
                break;
            default:
                // we need to merge entities here
                this.mergeCount += entities.size() - 1;
                Entity merge = entities.get(0);
                for (int i = 1; i < entities.size(); i++) {
                    Entity temp = entities.get(i);
                    // remove from entitySet
                    this.entitySet.remove(temp);
                    // merge names
                    merge.names.addAll(temp.names);
                    // merge frequency
                    merge.frequency += temp.frequency;
                    // merge neighbor
                    for (Map.Entry<Entity, Integer> nb : temp.neighborInteract.entrySet()) {
                        if (merge.neighborInteract.containsKey(nb.getKey())) {
                            merge.neighborInteract.put(nb.getKey(), merge.neighborInteract.get(nb.getKey()) + nb.getValue());
                        }
                    }
                }
                // delete itself from neighbors
                entities.forEach(e -> merge.neighborInteract.remove(e));
                entity = merge;
                break;
        }

        entitySet.add(entity);
        entity.names.addAll(cluster_names);
        for (String name : cluster_names) {
            entityNameMap.put(name, entity);
        }

        entity.frequency += appearCount;
        return entity;
    }


    public int entityNumber() {
        return this.entityCount - mergeCount;
    }

    public String report() {
        StringBuilder sb = new StringBuilder("Total entity numbers: " + this.entityNumber() + "\n\n");
        List<Entity> entityList = entitySet.stream().sorted((o1, o2) -> o2.frequency - o1.frequency).collect(Collectors.toList());

        sb.append("Entities sorted by frequency:").append("\n");
        entityList.forEach(o -> sb.append(String.format("%s\t%d\n", String.join(",", o.names), o.frequency)));

        sb.append("\n\nInteraction\n");
        for (Entity e : entityList) {
            sb.append("===========================\n");
            sb.append(e.toString()).append("\n").append("-----------------\n");
            for (Map.Entry<Entity, Integer> entry : e.neighborInteract.entrySet()) {
                sb.append(entry.getKey().toString()).append("\t").append(entry.getValue()).append("\n");
            }
        }

        return sb.toString();
    }
}

class Entity {
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


class MentionToken {
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

