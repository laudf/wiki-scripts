#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
  wiki_dump_parser.py

  Script to convert a xml mediawiki history dump to a csv file with readable useful data
for pandas processing.

  Copyright 2017-2019 Abel 'Akronix' Serrano Juste <akronix5@gmail.com>
"""

import xml.parsers.expat
import sys
from bs4 import BeautifulSoup
import nltk
import pandas as pd
nltk.download('punkt')
import re
from factoids import generate_factoids
#import wikitextparser as wtp

__version__ = '2.0.1'

Debug = False

csv_separator = ","

def xml_to_csv(filename):

  ### BEGIN xmt_to_csv var declarations ###
  # Shared variables for parser subfunctions:
  ## output_csv, _current_tag, _parent
  ## page_id,page_title,page_ns,revision_id,timestamp,contributor_id,contributor_name,bytes_var

  output_csv = None
  _parent = None
  _current_tag = ''
  page_id = page_title = page_ns = revision_id = timestamp = contributor_id = contributor_name = bytes_var = edit_content = factoids = ''
  def filter_special_characters(data):
      translation_table = dict.fromkeys(map(ord, '|'), None)
      data_wtout_crt = data.translate(translation_table)
      data_wtout_crt = re.sub('<.*>', '', data_wtout_crt, flags=re.MULTILINE)
      #text_lower = data_wtout_crt.lower()
      text_clean = " ".join(data_wtout_crt.split())
      return text_clean

  def start_tag(tag, attrs):
    nonlocal output_csv, _current_tag, _parent
    nonlocal bytes_var

    _current_tag = tag

    if tag == 'text':
      if 'bytes' in attrs:
        bytes_var = attrs['bytes']
      else: # There's a 'deleted' flag or no info about bytes of the edition
        bytes_var = '-1'
      _parent = tag
    elif tag == 'page' or tag == 'revision' or tag == 'contributor':
      _parent = tag

    if tag == 'upload':
      print("!! Warning: '<upload>' element not being handled", file=sys.stderr)

  def data_handler(data):
    nonlocal output_csv, _current_tag, _parent
    nonlocal page_id,page_title,page_ns,revision_id,timestamp,contributor_id,contributor_name,edit_content,factoids

    if _current_tag == '': # Don't process blank "orphan" data between tags!!
      return

    if _parent:
      if _parent == 'page':
        if _current_tag == 'title':
          page_title ='|' +  data + '|' 
        elif _current_tag == 'id':
          page_id = data
          if Debug:
            print("Parsing page " + page_id )
        elif _current_tag == 'ns':
          page_ns = data
      elif _parent == 'revision':
        if _current_tag == 'id':
          revision_id = data
        elif _current_tag == 'timestamp':
          timestamp = data
      elif _parent == 'contributor':
        if _current_tag == 'id':
          contributor_id = data
        elif _current_tag == 'username':
          contributor_name = '|' + data + '|'
        elif _current_tag == 'ip':
          contributor_id = data
          contributor_name = 'Anonymous'
      elif _parent == 'text':
          edit_content = '|' + filter_special_characters(data) + '|'
          factoids = '|' + generate_factoids(edit_content) + '|'

  def end_tag(tag):
    nonlocal output_csv, _current_tag, _parent
    nonlocal page_id,page_title,page_ns,revision_id,timestamp,contributor_id,contributor_name,bytes_var,edit_content,factoids


    def has_empty_field(l):
      field_empty = False;
      i = 0
      while (not field_empty and i<len(l)):
        field_empty = (l[i] == '');
        i = i + 1
      return field_empty


    # uploading one level of parent if any of these tags close
    if tag == 'page':
      _parent = None
    elif tag == 'revision':
      _parent = 'page'
    elif tag == 'contributor':
      _parent = 'revision'
    elif tag == 'text':
      _parent = 'revision'

    # print revision to revision output csv
    if tag == 'revision':

      revision_row = [page_id, page_title, page_ns,
                      revision_id, timestamp,
                      contributor_id,contributor_name,
                      bytes_var,edit_content, factoids]

      # Do not print (skip) revisions that has any of the fields not available
      if not has_empty_field(revision_row):
        output_csv.write(csv_separator.join(revision_row) + '\n')
      else:
        print("The following line has imcomplete info and therefore it's been removed from the dataset:")
        print(revision_row)

      # Debug lines to standard output
      if Debug:
        print(csv_separator.join(revision_row))

      # Clearing data that has to be recalculated for every row:
      revision_id = timestamp = contributor_id = contributor_name = bytes_var = edit_content =  factoids = ''

    _current_tag = '' # Very important!!! Otherwise blank "orphan" data between tags remain in _current_tag and trigger data_handler!! >:(


  ### BEGIN xml_to_csv body ###

  # Initializing xml parser
  parser = xml.parsers.expat.ParserCreate()
  input_file = open(filename, 'rb')
  print(input_file)
  parser.StartElementHandler = start_tag
  parser.EndElementHandler = end_tag
  parser.CharacterDataHandler = data_handler
  parser.buffer_text = True
  #parser.buffer_size = 2048

  # writing header for output csv file
  csv_name = filename[0:-3]+"csv"
  output_csv = open(csv_name,'w', encoding='utf8')
  output_csv.write(csv_separator.join(["page_id","page_title","page_ns","revision_id","timestamp","contributor_id","contributor_name","bytes","edit_content","factoids"]))
  output_csv.write("\n")

  # Parsing xml and writting proccesed data to output csv
  print("Processing...")
  parser.ParseFile(input_file)
  print("Done processing")

  input_file.close()
  output_csv.close()

  return True


if __name__ == "__main__":
  if(len(sys.argv)) >= 2:
    print ('Dump files to process: {}'.format(sys.argv[1:]))
    for xmlfile in sys.argv[1:]:
      print("Starting to parse file " + xmlfile)
      if xml_to_csv(xmlfile):
        print("Data dump {} parsed succesfully".format(xmlfile))
  else:
    print("Error: Invalid number of arguments. Please specify one or more .xml file to parse", file=sys.stderr)
