BEGIN;
CREATE TABLE `lims_laboratory` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `name` varchar(600) NOT NULL,
    `address` varchar(600) NOT NULL,
    `city` varchar(180) NOT NULL,
    `postal_code` varchar(30) NOT NULL,
    `country` varchar(180) NOT NULL,
    `contact_phone` varchar(60) NOT NULL,
    `contact_fax` varchar(60) NOT NULL,
    `organisation` varchar(600) NULL,
    `created` datetime NOT NULL,
    `modified` datetime NOT NULL
)
;
CREATE TABLE `lims_project` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `user_id` integer NOT NULL UNIQUE,
    `name` varchar(50) NOT NULL,
    `title` varchar(200) NOT NULL,
    `summary` longtext NOT NULL,
    `beam_time` double precision NOT NULL,
    `lab_id` integer NOT NULL,
    `start_date` date NOT NULL,
    `end_date` date NOT NULL,
    `created` datetime NOT NULL,
    `modified` datetime NOT NULL
)
;
ALTER TABLE `lims_project` ADD CONSTRAINT user_id_refs_id_4069d37e0e8790ad FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `lims_project` ADD CONSTRAINT lab_id_refs_id_45c7640aa96e8174 FOREIGN KEY (`lab_id`) REFERENCES `lims_laboratory` (`id`);
CREATE TABLE `lims_beamusage` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `project_id` integer NOT NULL,
    `start_time` datetime NOT NULL,
    `end_time` datetime NOT NULL,
    `description` varchar(200) NOT NULL
)
;
ALTER TABLE `lims_beamusage` ADD CONSTRAINT project_id_refs_id_30711422fb85d25e FOREIGN KEY (`project_id`) REFERENCES `lims_project` (`id`);
CREATE TABLE `lims_constituent` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `project_id` integer NOT NULL,
    `name` varchar(60) NOT NULL,
    `acronym` varchar(20) NOT NULL,
    `source` integer NOT NULL,
    `kind` integer NOT NULL,
    `is_radioactive` bool NOT NULL,
    `is_contaminant` bool NOT NULL,
    `is_toxic` bool NOT NULL,
    `is_oxidising` bool NOT NULL,
    `is_explosive` bool NOT NULL,
    `is_corrosive` bool NOT NULL,
    `is_inflamable` bool NOT NULL,
    `is_biological_hazard` bool NOT NULL,
    `hazard_details` longtext NOT NULL,
    `created` datetime NOT NULL,
    `modified` datetime NOT NULL
)
;
ALTER TABLE `lims_constituent` ADD CONSTRAINT project_id_refs_id_1413e5d2d73864c FOREIGN KEY (`project_id`) REFERENCES `lims_project` (`id`);
CREATE TABLE `lims_carrier` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `name` varchar(60) NOT NULL,
    `phone_number` varchar(20) NOT NULL,
    `fax_number` varchar(20) NOT NULL,
    `code_regex` varchar(60) NOT NULL,
    `url` varchar(200) NOT NULL
)
;
CREATE TABLE `lims_shipment` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `project_id` integer NOT NULL,
    `label` varchar(60) NOT NULL,
    `comments` longtext NULL,
    `tracking_code` varchar(60) NULL,
    `return_code` varchar(60) NULL,
    `date_shipped` datetime NULL,
    `date_received` datetime NULL,
    `date_returned` datetime NULL,
    `status` integer NOT NULL,
    `carrier_id` integer NULL,
    `created` datetime NOT NULL,
    `modified` datetime NOT NULL
)
;
ALTER TABLE `lims_shipment` ADD CONSTRAINT project_id_refs_id_6c2ee27e703b2e0d FOREIGN KEY (`project_id`) REFERENCES `lims_project` (`id`);
ALTER TABLE `lims_shipment` ADD CONSTRAINT carrier_id_refs_id_687ca49dbe9d16e0 FOREIGN KEY (`carrier_id`) REFERENCES `lims_carrier` (`id`);
CREATE TABLE `lims_dewar` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `project_id` integer NOT NULL,
    `label` varchar(60) NOT NULL,
    `code` varchar(150) NOT NULL,
    `comments` longtext NULL,
    `storage_location` varchar(60) NULL,
    `shipment_id` integer NULL,
    `created` datetime NOT NULL,
    `modified` datetime NOT NULL
)
;
ALTER TABLE `lims_dewar` ADD CONSTRAINT project_id_refs_id_4adf443d0bd5cb67 FOREIGN KEY (`project_id`) REFERENCES `lims_project` (`id`);
ALTER TABLE `lims_dewar` ADD CONSTRAINT shipment_id_refs_id_7a05d577d10890c1 FOREIGN KEY (`shipment_id`) REFERENCES `lims_shipment` (`id`);
CREATE TABLE `lims_container` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `project_id` integer NOT NULL,
    `label` varchar(60) NOT NULL,
    `code` varchar(50) NULL,
    `kind` integer NOT NULL,
    `dewar_id` integer NULL,
    `comments` longtext NULL,
    `created` datetime NOT NULL,
    `modified` datetime NOT NULL
)
;
ALTER TABLE `lims_container` ADD CONSTRAINT project_id_refs_id_ee118ff1eabb58d FOREIGN KEY (`project_id`) REFERENCES `lims_project` (`id`);
ALTER TABLE `lims_container` ADD CONSTRAINT dewar_id_refs_id_2a2ac81412feb637 FOREIGN KEY (`dewar_id`) REFERENCES `lims_dewar` (`id`);
CREATE TABLE `lims_spacegroup` (
    `id` integer NOT NULL PRIMARY KEY,
    `name` varchar(20) NOT NULL,
    `crystal_system` varchar(1) NOT NULL,
    `lattice_type` varchar(1) NOT NULL
)
;
CREATE TABLE `lims_crystalform` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `project_id` integer NOT NULL,
    `name` varchar(60) NOT NULL,
    `space_group_id` integer NULL,
    `cell_a` double precision NULL,
    `cell_b` double precision NULL,
    `cell_c` double precision NULL,
    `cell_alpha` double precision NULL,
    `cell_beta` double precision NULL,
    `cell_gamma` double precision NULL,
    `created` datetime NOT NULL,
    `modified` datetime NOT NULL
)
;
ALTER TABLE `lims_crystalform` ADD CONSTRAINT project_id_refs_id_e76826a32327e2a FOREIGN KEY (`project_id`) REFERENCES `lims_project` (`id`);
ALTER TABLE `lims_crystalform` ADD CONSTRAINT space_group_id_refs_id_113e59a1495b7495 FOREIGN KEY (`space_group_id`) REFERENCES `lims_spacegroup` (`id`);
CREATE TABLE `lims_cocktail` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `project_id` integer NOT NULL,
    `comments` longtext NULL,
    `created` datetime NOT NULL,
    `modified` datetime NOT NULL
)
;
ALTER TABLE `lims_cocktail` ADD CONSTRAINT project_id_refs_id_3340c9699389bb5d FOREIGN KEY (`project_id`) REFERENCES `lims_project` (`id`);
CREATE TABLE `lims_crystal` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `project_id` integer NOT NULL,
    `name` varchar(60) NOT NULL,
    `code` varchar(50) NULL,
    `crystal_form_id` integer NULL,
    `pin_length` integer NOT NULL,
    `loop_size` double precision NULL,
    `cocktail_id` integer NOT NULL,
    `container_id` integer NULL,
    `container_location` varchar(10) NULL,
    `comments` longtext NULL,
    `created` datetime NOT NULL,
    `modified` datetime NOT NULL,
    UNIQUE (`project_id`, `container_id`, `container_location`),
    UNIQUE (`project_id`, `name`)
)
;
ALTER TABLE `lims_crystal` ADD CONSTRAINT project_id_refs_id_3f8e6f15643797d4 FOREIGN KEY (`project_id`) REFERENCES `lims_project` (`id`);
ALTER TABLE `lims_crystal` ADD CONSTRAINT crystal_form_id_refs_id_c267e94f9147403 FOREIGN KEY (`crystal_form_id`) REFERENCES `lims_crystalform` (`id`);
ALTER TABLE `lims_crystal` ADD CONSTRAINT container_id_refs_id_6f4853255669c5d4 FOREIGN KEY (`container_id`) REFERENCES `lims_container` (`id`);
ALTER TABLE `lims_crystal` ADD CONSTRAINT cocktail_id_refs_id_dbfaa9438bc1c84 FOREIGN KEY (`cocktail_id`) REFERENCES `lims_cocktail` (`id`);
CREATE TABLE `lims_experiment` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `project_id` integer NOT NULL,
    `name` varchar(60) NOT NULL,
    `hi_res` double precision NULL,
    `lo_res` double precision NULL,
    `i_sigma` double precision NULL,
    `r_meas` double precision NULL,
    `multiplicity` integer NULL,
    `energy` numeric(10, 4) NULL,
    `kind` integer NOT NULL,
    `absorption_edge` varchar(5) NULL,
    `plan` integer NOT NULL,
    `comments` longtext NULL,
    `status` integer NOT NULL,
    `created` datetime NOT NULL,
    `modified` datetime NOT NULL
)
;
ALTER TABLE `lims_experiment` ADD CONSTRAINT project_id_refs_id_16704b37047b7358 FOREIGN KEY (`project_id`) REFERENCES `lims_project` (`id`);
CREATE TABLE `lims_result` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `project_id` integer NOT NULL,
    `experiment_id` integer NOT NULL,
    `crystal_id` integer NOT NULL,
    `url` varchar(200) NOT NULL,
    `state` integer NOT NULL,
    `created` datetime NOT NULL,
    `modified` datetime NOT NULL
)
;
ALTER TABLE `lims_result` ADD CONSTRAINT project_id_refs_id_63a2d95146607f06 FOREIGN KEY (`project_id`) REFERENCES `lims_project` (`id`);
ALTER TABLE `lims_result` ADD CONSTRAINT experiment_id_refs_id_5772047b0ebb5289 FOREIGN KEY (`experiment_id`) REFERENCES `lims_experiment` (`id`);
ALTER TABLE `lims_result` ADD CONSTRAINT crystal_id_refs_id_6032a7a39a69ef63 FOREIGN KEY (`crystal_id`) REFERENCES `lims_crystal` (`id`);
CREATE TABLE `lims_activitylog` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `created` datetime NOT NULL,
    `project_id` integer NOT NULL,
    `user_id` integer NOT NULL,
    `ip_number` char(15) NOT NULL,
    `content_type_id` integer NULL,
    `object_id` varchar(20) NULL,
    `object_repr` varchar(200) NULL,
    `action_type` integer NOT NULL,
    `description` longtext NOT NULL
)
;
ALTER TABLE `lims_activitylog` ADD CONSTRAINT project_id_refs_id_565baef018c9384d FOREIGN KEY (`project_id`) REFERENCES `lims_project` (`id`);
ALTER TABLE `lims_activitylog` ADD CONSTRAINT user_id_refs_id_fd87961cfedf575 FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `lims_activitylog` ADD CONSTRAINT content_type_id_refs_id_7965ab3ed730d1c9 FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`);
CREATE TABLE `lims_cocktail_constituents` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `cocktail_id` integer NOT NULL,
    `constituent_id` integer NOT NULL,
    UNIQUE (`cocktail_id`, `constituent_id`)
)
;
ALTER TABLE `lims_cocktail_constituents` ADD CONSTRAINT cocktail_id_refs_id_1f5460efdcc6a38c FOREIGN KEY (`cocktail_id`) REFERENCES `lims_cocktail` (`id`);
ALTER TABLE `lims_cocktail_constituents` ADD CONSTRAINT constituent_id_refs_id_205914926274d72f FOREIGN KEY (`constituent_id`) REFERENCES `lims_constituent` (`id`);
CREATE TABLE `lims_experiment_crystals` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `experiment_id` integer NOT NULL,
    `crystal_id` integer NOT NULL,
    UNIQUE (`experiment_id`, `crystal_id`)
)
;
ALTER TABLE `lims_experiment_crystals` ADD CONSTRAINT experiment_id_refs_id_7e61b9d3f5c3a100 FOREIGN KEY (`experiment_id`) REFERENCES `lims_experiment` (`id`);
ALTER TABLE `lims_experiment_crystals` ADD CONSTRAINT crystal_id_refs_id_4dd369a23204ed14 FOREIGN KEY (`crystal_id`) REFERENCES `lims_crystal` (`id`);
CREATE INDEX `lims_project_name` ON `lims_project` (`name`);
CREATE INDEX `lims_project_lab_id` ON `lims_project` (`lab_id`);
CREATE INDEX `lims_beamusage_project_id` ON `lims_beamusage` (`project_id`);
CREATE INDEX `lims_constituent_project_id` ON `lims_constituent` (`project_id`);
CREATE INDEX `lims_constituent_acronym` ON `lims_constituent` (`acronym`);
CREATE INDEX `lims_shipment_project_id` ON `lims_shipment` (`project_id`);
CREATE INDEX `lims_shipment_carrier_id` ON `lims_shipment` (`carrier_id`);
CREATE INDEX `lims_dewar_project_id` ON `lims_dewar` (`project_id`);
CREATE INDEX `lims_dewar_shipment_id` ON `lims_dewar` (`shipment_id`);
CREATE INDEX `lims_container_project_id` ON `lims_container` (`project_id`);
CREATE INDEX `lims_container_code` ON `lims_container` (`code`);
CREATE INDEX `lims_container_dewar_id` ON `lims_container` (`dewar_id`);
CREATE INDEX `lims_crystalform_project_id` ON `lims_crystalform` (`project_id`);
CREATE INDEX `lims_crystalform_space_group_id` ON `lims_crystalform` (`space_group_id`);
CREATE INDEX `lims_cocktail_project_id` ON `lims_cocktail` (`project_id`);
CREATE INDEX `lims_crystal_project_id` ON `lims_crystal` (`project_id`);
CREATE INDEX `lims_crystal_code` ON `lims_crystal` (`code`);
CREATE INDEX `lims_crystal_crystal_form_id` ON `lims_crystal` (`crystal_form_id`);
CREATE INDEX `lims_crystal_cocktail_id` ON `lims_crystal` (`cocktail_id`);
CREATE INDEX `lims_crystal_container_id` ON `lims_crystal` (`container_id`);
CREATE INDEX `lims_experiment_project_id` ON `lims_experiment` (`project_id`);
CREATE INDEX `lims_result_project_id` ON `lims_result` (`project_id`);
CREATE INDEX `lims_result_experiment_id` ON `lims_result` (`experiment_id`);
CREATE INDEX `lims_result_crystal_id` ON `lims_result` (`crystal_id`);
CREATE INDEX `lims_activitylog_project_id` ON `lims_activitylog` (`project_id`);
CREATE INDEX `lims_activitylog_user_id` ON `lims_activitylog` (`user_id`);
CREATE INDEX `lims_activitylog_content_type_id` ON `lims_activitylog` (`content_type_id`);
COMMIT;
