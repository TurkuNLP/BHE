#!/bin/bash


############
# Settings #
############


main_dir=/media/suwisa/BB3/system_test

main_tool=/home/suwisa
genia_dir=$main_tool/geniass
nersuite_dir=$main_tool/nersuite-master

script_dir=$main_tool/trunk/BB3_release

in_dir=$main_dir/input
out_dir=$main_dir/output
temp_dir=$main_dir/temp


##################
# Pre-processing #
##################

# mkdir $out_dir

cd $in_dir
ls *.txt > $temp_dir/text.lst 
for f in `cat $temp_dir/text.lst`
do
    echo 'processing...' $f
    in_f=$in_dir/$f
    out_f=$temp_dir/$f
    cd $script_dir
    python rewriteu2a.py $in_f -d $out_f
    cd $genia_dir
    ./geniass $out_f $out_f.gss
    perl geniass-postproc.pl $out_f.gss > $out_f.per
    cd $nersuite_dir
    nersuite_tokenizer < $out_f.per | nersuite_gtagger -d $nersuite_dir/models/gtagger > $out_f.gtag
    cd $script_dir
    python fix_offset.py -f $out_f
    cp $out_f.off $out_f.off.guzzy
    echo ''
done


#############
# Geography #
#############

geo_dict=$main_dir/dict/geographic_area.cdbpp
geo_dir=$temp_dir/geographical
tag_ext=.off
ext=.geo
c=1
b=0.5
ent=Geo

mkdir $geo_dir
model_geo=$main_dir/models/BB2_task_2_train_dev_test_BB3_event+ner_train_dev.m

ls $temp_dir/*$tag_ext > $temp_dir/geo_off.lst
cd $nersuite_dir

for f in `cat $temp_dir/geo_off.lst`
do
    echo $f
    nersuite_dic_tagger $geo_dict < $f | nersuite tag -C $c -b B-$ent:$b -m $model_geo > $f$ext
    cd $script_dir
    python write_a1_result.py -f $f$ext -e $ext -t $tag_ext
done


###########
# Habitat #
###########

habitat_dict=$main_dir/dict/ontobiotope.cdbpp
hab_dir=$temp_dir/habitat
tag_ext=.off.fuzzy
ext=.hab
c=0.0078125
b=3.0
ent=Hab

mkdir $hab_dir
model_hab=$main_dir/models/BioNLP-ST-2016_BB-cat+ner_train_dev.hab.fuzzy.m

cd /media/suwisa/BB3/system_test/bacteria_biotope/
python fuzzy_matching.py -i $temp_dir -e Habitat -c 2 -f .off

ls $temp_dir/*$tag_ext > $temp_dir/hab_off.lst
cd $nersuite_dir

for f in `cat $temp_dir/hab_off.lst`
do
    echo $f
    nersuite_dic_tagger $habitat_dict < $f | nersuite tag -C $c -b B-$ent:$b -m $model_hab > $f$ext
    cd $script_dir
    python write_a1_result.py -f $f$ext -e $ext -t $tag_ext
done


############
# Bacteria #
############

bacteria_dict=$main_dir/dict/bact_sci_name.cdbpp
bac_dir=$temp_dir/bacteria
tag_ext=.off
ext=.bac
c=0.00390625
b=2.5
ent=Bac

mkdir $bac_dir
model_bac=$main_dir/models/BB1_train_dev_BB3_cat+ner_train_dev.m

cd /media/suwisa/BB3/system_test/bacteria_biotope/

ls $temp_dir/*$tag_ext > $temp_dir/bac_off.lst

cd $nersuite_folder

for f in `cat $temp_dir/bac_off.lst`
do
    echo $f
    nersuite_dic_tagger $bacteria_dict < $f | nersuite tag -C $c -b B-$ent:$b -m $model_bac > $f$ext
    cd $script_dir
    python write_a1_result.py -f $f$ext -e $ext -t $tag_ext
done


######################
# combine prediction #
######################

cd $script_dir
python merged_entities.py -i $temp_dir -o $out_dir
