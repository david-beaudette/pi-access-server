/* Find access related entries in civicrm_tag table */
SELECT  `civicrm_tag`.`id`,
        `civicrm_tag`.`name`,
        `civicrm_tag`.`description`,
        `civicrm_tag`.`used_for`,
        `civicrm_tag`.`created_id`,
        `civicrm_tag`.`created_date`
FROM    `sherbro3_civicrm`.`civicrm_tag`;
/*WHERE `civicrm_tag`.`parent_id` =  (SELECT `civicrm_tag`.`id`
									FROM `sherbro3_civicrm`.`civicrm_tag`
									WHERE `civicrm_tag`.`name` = 'Accès');

/* Find related entries in contact to tag link table (civicrm_entity) */
SELECT * FROM `sherbro3_civicrm`.`civicrm_entity_tag`

