##usage

pls install [neuralcoref](https://github.com/huggingface/neuralcoref),and [spaCy](https://spacy.io/)

## pipeline

### split into sections
split text into section, given granularity as a param (default split into paragarph)
Note that the granularity is important because we only do corefence(pronoun resolve) inside a section. But also we can design better algo to handle coref among different section.

### section.foreach

#### 1. parseEntity

we do Coref and NER here

the coref has a bug that it will skip those named entity without reference from pronoun

for example,

`David is a boy and he is handsome. ` will produce `['David','he']`

while `David is a boy` will produce nothing

So we combine Coref and NER to identify all entity.


#### 2. parseRelationship

parse relationship between entities in a section.

two basic rule: 
a) in same sentence.  b) within X words, X is a threshold


## issue
1. need too handle coreference of named entity among different section.

	For example, "Harry Potter" appear in section1, "Potter" appear in section2, we need to merge them together. (If they appear in the same section, the coref can potentially handle this)
	
2. how to decide granularity, some paragraph are all dialogs, and some doesn't contain any name.