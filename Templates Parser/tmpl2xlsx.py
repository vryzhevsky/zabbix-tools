#!/usr/bin/env python

import sys
import os
import json
import logging
import logging.handlers
import xmltodict
import xlsxwriter

log_level = logging.DEBUG


def tmpl2xlsx(infile, xlsx_dir, workbook):
    logger = logging.getLogger('tom')
    logger.info("Processing file %s" % infile)

    with open(infile, 'r', encoding="utf-8") as f:
        file_content = f.read()
        f.close

    # logger.debug("Content of file:\n%s" % file_content)
    content = xmltodict.parse(file_content)
    pcontent = json.dumps(content, indent=4, separators=(',', ': '))
    logger.debug("Parsed content:\n%s" % pcontent)
    content = json.loads(pcontent)

    templates = content['zabbix_export']['templates']['template']
    if type(templates) is dict:
        templates = [templates]
    # triggers = content['zabbix_export']['triggers']
    # graphs = content['zabbix_export']['graphs']
    # value_maps = content['zabbix_export']['value_maps']

    bold = workbook.add_format(
        {
            'bold': True
            }
        )
    item_header = workbook.add_format(
        {
            'bg_color': '#CCCCCC',
            'bold': True,
            'border': 1
            }
        )
    item_text = workbook.add_format(
        {
            'border': 1
            }
        )
    trigger_severity = {
        '0': workbook.add_format({'bg_color': '#97AAB3'}),
        '1': workbook.add_format({'bg_color': '#7499FF'}),
        '2': workbook.add_format({'bg_color': '#FFC859'}),
        '3': workbook.add_format({'bg_color': '#FFA059'}),
        '4': workbook.add_format({'bg_color': '#E97659'}),
        '5': workbook.add_format({'bg_color': '#E45959'}),
        # '0' : workbook.add_format({'bg_color' : '#97AAB3'}),
        'INFO': workbook.add_format({'bg_color': '#7499FF'}),
        'WARNING': workbook.add_format({'bg_color': '#FFC859'}),
        'AVERAGE': workbook.add_format({'bg_color': '#FFA059'}),
        'HIGH': workbook.add_format({'bg_color': '#E97659'}),
        'DISASTER': workbook.add_format({'bg_color': '#E45959'})
    }

    for template in templates:
        logger.info("Processing template '%s'" % template['template'])
        logger.info("Adding worksheet")
        max_length_A = 0
        max_length_B = 0
        max_length_C = 0
        try:
            worksheet = workbook.add_worksheet(template['template'][0:30])
        except Exception as ex:
            logger.error("Error while adding worksheet")
            logger.error(ex)
            continue

        logger.info("Adding title and common info about template")
        worksheet.write('A1', template['name'], bold)
        worksheet.write('A2', template.get('description', 'No description'))

        worksheet.write('A4', "Items:", bold)
        worksheet.write('A5', "Name", item_header)
        worksheet.write('B5', "Key", item_header)
        worksheet.write('C5', "Description", item_header)

        logger.info("Adding System Items")
        worksheet.merge_range('A6:C6', "System items", item_header)

        index = 7
        if 'items' in template:
            items = template['items']['item']
            if type(items) is dict:
                items = [items]

            for item in items:
                worksheet.write('A%s' % index, item['name'], item_text)
                worksheet.write('B%s' % index, item['key'], item_text)
                worksheet.write('C%s' % index, item.get('description', ''),
                                item_text)
                max_length_A = max(max_length_A, len(item['name']))
                max_length_B = max(max_length_B, len(item['key']))
                max_length_C = max(max_length_C,
                                   len(str(item.get('description', ''))))
                index = index + 1

        worksheet.set_column('A:A', max_length_A)
        worksheet.set_column('B:B', max_length_B)
        worksheet.set_column('C:C', max_length_C)

        logger.info("Adding Discovery rules")

        if 'discovery_rules' in template:
            if template['discovery_rules'] is None:
                continue
            drs = template['discovery_rules']['discovery_rule']
            if type(drs) is dict:
                drs = [drs]

            for dr in drs:
                logger.info("Processing rule '%s'" % dr['name'])

                worksheet.merge_range('A%s:C%s' % (index, index),
                                      dr['name'], item_header)
                index = index + 1

                logger.info("Adding item prototypes")

                if 'item_prototypes' in dr:
                    items = dr['item_prototypes']['item_prototype']
                    if type(items) is dict:
                        items = [items]

                    for item in items:
                        worksheet.write('A%s' % index, item['name'], item_text)
                        worksheet.write('B%s' % index, item['key'], item_text)
                        worksheet.write('C%s' % index,
                                        item.get('description', ''), item_text)
                        max_length_A = max(max_length_A, len(item['name']))
                        max_length_B = max(max_length_B, len(item['key']))
                        max_length_C = max(
                            max_length_C,
                            len(str(item.get('description', '')))
                            )
                        index = index + 1

        else:
            logger.info("No discovery rules found. Go to triggers")

        logger.info("Adding triggers")

        index = index + 1
        worksheet.write('A%s' % index, "Triggers:", bold)
        index = index + 1
        worksheet.write('A%s' % index, "Name", item_header)
        worksheet.write('B%s' % index, "Expression", item_header)
        worksheet.write('C%s' % index, "Severity", item_header)

        index = index + 1
        logger.info("Adding System Triggers")
        worksheet.merge_range(
            'A%s:C%s' % (index, index), "System triggers", item_header)

        index = index + 1
        if "triggers" in content['zabbix_export']:
            triggers = content['zabbix_export']['triggers']['trigger']
            if type(triggers) is dict:
                triggers = [triggers]

            for trigger in triggers:
                logger.info("Adding system trigger %s" % trigger['name'])
                worksheet.write('A%s' % index, trigger['name'],
                                trigger_severity[trigger['priority']])
                worksheet.write('B%s' % index, trigger['expression'],
                                trigger_severity[trigger['priority']])
                worksheet.write('C%s' % index, trigger['priority'],
                                trigger_severity[trigger['priority']])
                max_length_A = max(max_length_A, len(trigger['name']))
                max_length_B = max(max_length_B, len(trigger['expression']))
                max_length_C = max(max_length_C, len('Description'))
                index = index + 1

        logger.info("Adding triggers from items")
        if 'items' in template:
            items = template['items']['item']
            if type(items) is dict:
                items = [items]

            for item in items:
                if "triggers" in item:
                    triggers = item['triggers']['trigger']
                    if type(triggers) is dict:
                        triggers = [triggers]
                    for trigger in triggers:
                        logger.info(
                            "Adding item trigger <%s>" % trigger['name'])
                        trigger_exp = trigger['expression'].replace(":", "-")
                        logger.info(trigger_exp)
                        worksheet.write('A%s' % index, trigger['name'],
                                        trigger_severity[trigger['priority']])
                        worksheet.write('B%s' % index, trigger_exp,
                                        trigger_severity[trigger['priority']])
                        worksheet.write('C%s' % index, trigger['priority'],
                                        trigger_severity[trigger['priority']])
                        max_length_A = max(max_length_A, len(trigger['name']))
                        max_length_B = max(max_length_B,
                                           len(trigger['expression']))
                        max_length_C = max(max_length_C, len('Description'))
                        index = index + 1

        logger.info("Adding Discovery rules")

        if 'discovery_rules' in template:
            drs = template['discovery_rules']['discovery_rule']
            if type(drs) is dict:
                drs = [drs]

            for dr in drs:
                logger.info("Processing rule '%s'" % dr['name'])

                worksheet.merge_range('A%s:C%s' % (index, index),
                                      dr['name'], item_header)
                index = index + 1

                logger.info("Adding trigger prototypes")

                if 'trigger_prototypes' in dr:
                    triggers = dr['trigger_prototypes']['trigger_prototype']
                    if type(triggers) is dict:
                        triggers = [triggers]

                    for trigger in triggers:
                        worksheet.write('A%s' % index, trigger['name'],
                                        trigger_severity[trigger['priority']])
                        worksheet.write('B%s' % index, trigger['expression'],
                                        trigger_severity[trigger['priority']])
                        worksheet.write('C%s' % index, trigger['priority'],
                                        trigger_severity[trigger['priority']])
                        max_length_A = max(max_length_A, len(trigger['name']))
                        max_length_B = max(max_length_B,
                                           len(trigger['expression']))
                        max_length_C = max(max_length_C, len('Description'))
                        index = index + 1

                logger.info("Adding trigger prototypes from item prototypes")
                if 'item_prototypes' in dr:
                    items = dr['item_prototypes']['item_prototype']
                    if type(items) is dict:
                        items = [items]

                    for item in items:
                        triggers = []
                        if "trigger_prototypes" in item:
                            triggers =\
                                item['trigger_prototypes']['trigger_prototype']
                        if type(triggers) is dict:
                            triggers = [triggers]
                        for trigger in triggers:
                            logger.info(
                                "Adding item trigger <%s>" % trigger['name'])
                            trigger_exp = trigger['expression'].\
                                replace(":", "-")
                            logger.info(trigger_exp)
                            worksheet.write(
                                'A%s' % index, trigger['name'],
                                trigger_severity[trigger['priority']])
                            worksheet.write(
                                'B%s' % index, trigger_exp,
                                trigger_severity[trigger['priority']])
                            worksheet.write(
                                'C%s' % index, trigger['priority'],
                                trigger_severity[trigger['priority']])
                            max_length_A = max(
                                max_length_A, len(trigger['name']))
                            max_length_B = max(
                                max_length_B, len(trigger['expression']))
                            max_length_C = max(
                                max_length_C, len('Description'))
                            index = index + 1

        else:
            logger.info("No discovery rules found. Go to next template")

    worksheet.set_column('A:A', max_length_A)
    worksheet.set_column('B:B', max_length_B)
    worksheet.set_column('C:C', max_length_C)


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
    log_file = "%s/tmpl2xlsx.log" % log_dir
    tmpl_dir = "templates"
    xlsx_dir = "excel"

    setup_logging(log_file)

    logger = logging.getLogger('tom')
    logger.info("Starting")

    tmpl_files = os.listdir(tmpl_dir)
    logger.info("Template files: %s" % tmpl_files)

    excelfile = '%s/items.xlsx' % xlsx_dir
    logger.info("Output file: %s" % excelfile)
    workbook = xlsxwriter.Workbook(excelfile)
    for tmpl_file in tmpl_files:
        infile = "%s/%s" % (tmpl_dir, tmpl_file)
        tmpl2xlsx(infile, xlsx_dir, workbook)

    workbook.close()

    logger.info("Done")
    print("Done")


if __name__ == "__main__":
    main()
