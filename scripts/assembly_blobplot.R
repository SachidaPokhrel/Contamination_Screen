#!/usr/bin/env Rscript
args <- commandArgs(trailingOnly=TRUE)
if('--help' %in% args){cat('Usage: assembly_blobplot.R contig_evidence.tsv OUTPUT_DIR\n');quit(status=0)}
if(length(args)!=2)stop('Expected input table and output directory')
library(ggplot2)
d <- read.delim(args[1],check.names=FALSE)
d$kraken_label <- gsub('_',' ',d$kraken_label,fixed=TRUE)
p <- ggplot(d,aes(x=gc,y=mean_depth+0.001,size=length,colour=kraken_label))+geom_point(alpha=.65)+scale_y_log10()+scale_size_area(max_size=12)+theme_bw()+labs(x='GC fraction (ACGT denominator)',y='Mean retained depth + 0.001 (log scale)',colour='Kraken contig assignment',size='Contig length (bp)',subtitle='Published assembly; full cleaned DNA reads; taxonomy assignments require validation')
for(ext in c('png','pdf'))ggsave(file.path(args[2],paste0('assembly_blobplot.',ext)),p,width=11,height=7,dpi=300,limitsize=FALSE)
