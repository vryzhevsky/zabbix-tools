#!/usr/bin/env python

import sys
import os
import re
import json
import logging
import logging.handlers
import xmltodict

log_level = logging.INFO

def tmpl2html(infile, html_dir):
    logger = logging.getLogger('tom')
    logger.info("Processing file %s" % infile)

    with open(infile, 'r') as f:
        file_content = f.read()
        f.close

    logger.debug("Content of file:\n%s" % file_content)
    content = xmltodict.parse(file_content)
    pcontent = json.dumps(content, indent=4, separators=(',', ': '))
    logger.debug("Parsed content:\n%s" % pcontent)
    content = json.loads(pcontent)

    templates = content['zabbix_export']['templates']['template']
    if type(templates) is dict:
        templates = [templates]
    #triggers = content['zabbix_export']['triggers']
    #graphs = content['zabbix_export']['graphs']
    #value_maps = content['zabbix_export']['value_maps']

    for template in templates:
        logger.info("Processing template '%s'" % template['template'])
        logger.info("Starting HTML file")
        outfile = "%s/%s.html" % (html_dir, template['template'])
        with open(outfile, 'w') as f:
            temp_str = ''.join([
                "<html>\n",
                "<head>\n",
                "  <style type='text/css'>\n",
                "    body {font-family: 'Lucida Console'; font-size: 13px;}\n",
                "    h1 {font-size: 150%;}\n",
                "    h2 {font-size: 120%;}\n",
                "    table {\n",
                "      border-collapse: collapse;\n",
                "      border: 2px solid;\n",
                "      border-spacing: 0;\n",
                "    }\n",
                "    td {border: 1px solid; padding: 3px; font-size: 13px;}\n",
                "    .headline {\n",
                "      background: #cccccc;\n",
                "      font-weight: bold;\n",
                "    }\n",
                "    .capacity {\n",
                "      background: #eeffee;\n",
                "    }\n",
                "    .health {\n",
                "      background: #ffeeee;\n",
                "    }\n",
                "    .inventory {\n",
                "      background: #eeeeff;\n",
                "    }\n",
                "    .perf {\n",
                "      background: #eeeeee;\n",
                "    }\n",
                "  </style>\n",
                "</head>\n",
                "<body>\n"
                ])
            f.write(temp_str)
            f.close
        
        with open(outfile, 'a') as f:
            logger.info("Adding title and common info about template")
            temp_str = "<h1>%s</h1>\n" % template['name']
            f.write(temp_str)

            temp_str = "  <h2>Description:</h2>\n"
            f.write(temp_str)

            temp_str = "    <p>%s</p>\n" % template['description']
            f.write(temp_str)

            '''
            logger.info("Adding Applications")
            temp_str = "  <h2>Applications:</h2>\n"
            f.write(temp_str)
            for application in templates['template']['applications']['application']:
                temp_str = "    %s<br>\n" % application['name']
                file_content = f.write(temp_str)
            '''    

            temp_str = "  <h2>Items:</h2>\n"
            f.write(temp_str)

            temp_str = ''.join([
                "  <table>\n",
                "    <thead>\n",
                "      <tr><td class='headline'>Name</td>",
                "<td class='headline'>Key</td></tr>\n",
                "    </thead>\n",
                "    <tbody>\n"
                ])
            f.write(temp_str)

            logger.info("Adding Items")
            temp_str = "      <tr><td class='headline' colspan='2'>System items</td></tr>\n"
            f.write(temp_str)

            if template['items']:
                items = template['items']['item']
                if type(items) is dict:
                    items = [items]

                for item in items:
                    if ".capacity." in item['key']:
                        tdstyle = "capacity"
                    elif ".health." in item['key']:
                        tdstyle = "health"
                    elif ".inventory." in item['key']:
                        tdstyle = "inventory"
                    elif ".perf." in item['key']:
                        tdstyle = "perf"
                    else:
                        tdstyle = ""
                    temp_str = ''.join([
                        "        <tr>",
                        "<td class='%s'>%s</td>" % (tdstyle, item['name']),
                        "<td class='%s'>%s</td>" % (tdstyle, item['key']),
                        "</tr>\n"
                        ])
                    f.write(temp_str)

            logger.info("Adding Discovery rules")

            if template['discovery_rules'] is None:
                logger.info("No discovery rules found. Go to next template")
                continue
            
            drs = template['discovery_rules']['discovery_rule']
            if type(drs) is dict:
                drs = [drs]

            for dr in drs:
                logger.info("Processing rule '%s'" % dr['name'])
                temp_str = "      <tr><td class='headline' colspan='2'>%s:</td></tr>\n" %\
                           dr['name']
                f.write(temp_str)
                
                logger.info("Adding item prototypes")

                if dr['item_prototypes']:
                    items = dr['item_prototypes']['item_prototype']
                    if type(items) is dict:
                        items = [items]

                    for item in items:
                        if ".capacity." in item['key']:
                            tdstyle = "capacity"
                        elif ".health." in item['key']:
                            tdstyle = "health"
                        elif ".inventory." in item['key']:
                            tdstyle = "inventory"
                        elif ".perf." in item['key']:
                            tdstyle = "perf"
                        else:
                            tdstyle = ""
                        temp_str = ''.join([
                            "        <tr>",
                            "<td class='%s'>%s</td>" % (tdstyle, item['name']),
                            "<td class='%s'>%s</td>" % (tdstyle, item['key']),
                            "</tr>\n"
                            ])
                        f.write(temp_str)

            temp_str = ''.join([
                "      </tbody>\n",
                "    </table>\n"
                ])
            f.write(temp_str)

            f.close

        logger.info("Finishing HTML file")
        with open(outfile, 'a') as f:
            temp_str = "\n</body>\n</html>"
            f.write(temp_str)
            f.close

def log_exception_handler(type, value, tb):
    logger = logging.getLogger('tom')
    logger.exception("Uncaught exception: {0}".format(str(value)))

def setup_logging(log_file):
    my_logger = logging.getLogger('tom')
    my_logger.setLevel(log_level)

    handler = logging.handlers.RotatingFileHandler(
                          log_file, maxBytes=5120000, backupCount=5)

    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s [%(process)d] %(message)s')
    handler.setFormatter(formatter)

    my_logger.addHandler(handler)

    sys.excepthook = log_exception_handler
 
    return
	
def main():
    global log_level
    log_dir = "logs"
    log_file = "%s/tmpl2html.log" % log_dir
    tmpl_dir = "templates"
    html_dir = "html"
    
    setup_logging(log_file)

    logger = logging.getLogger('tom')
    logger.info("Starting")

    tmpl_files = os.listdir(tmpl_dir)
    logger.info("Template files: %s" % tmpl_files)

    for tmpl_file in tmpl_files:
        infile = "%s/%s" % (tmpl_dir, tmpl_file)
        tmpl2html(infile, html_dir)
        
    logger.info("Done")

if __name__ == "__main__":
    main()
