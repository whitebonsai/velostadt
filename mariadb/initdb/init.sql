SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS abrechnung;
DROP TABLE IF EXISTS fahrt;
DROP TABLE IF EXISTS fahrzeuge;
DROP TABLE IF EXISTS zahlungsmittel;
DROP TABLE IF EXISTS fahrzeugtyp;
DROP TABLE IF EXISTS benutzer;
DROP TABLE IF EXISTS anbieter;

CREATE TABLE anbieter (
  anbieter_id   INT UNSIGNED NOT NULL AUTO_INCREMENT,
  name          VARCHAR(120) NOT NULL,
  e_mail        VARCHAR(254) NOT NULL,
  passwort_hash VARCHAR(255) NOT NULL,
  PRIMARY KEY (anbieter_id),
  UNIQUE KEY uq_anbieter_email (e_mail)
) ENGINE=InnoDB;

CREATE TABLE benutzer (
  benutzer_id   INT UNSIGNED NOT NULL AUTO_INCREMENT,
  vorname       VARCHAR(80)  NOT NULL,
  nachname      VARCHAR(80)  NOT NULL,
  e_mail        VARCHAR(254) NOT NULL,
  passwort_hash VARCHAR(255) NOT NULL,
  PRIMARY KEY (benutzer_id),
  UNIQUE KEY uq_benutzer_email (e_mail)
) ENGINE=InnoDB;

CREATE TABLE fahrzeugtyp (
  fahrzeugtyp_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  bezeichnung    VARCHAR(80)  NOT NULL,
  basispreis     DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  preis_pro_min  DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  PRIMARY KEY (fahrzeugtyp_id),
  CONSTRAINT chk_preise CHECK (basispreis >= 0 AND preis_pro_min >= 0)
) ENGINE=InnoDB;

CREATE TABLE fahrzeuge (
  fahrzeug_id    INT UNSIGNED NOT NULL AUTO_INCREMENT,
  anbieter_id    INT UNSIGNED NOT NULL,
  fahrzeugtyp_id INT UNSIGNED NOT NULL,
  akku_prozent   TINYINT UNSIGNED NOT NULL DEFAULT 0,
  status         VARCHAR(30) NOT NULL,
  gps_lat        DECIMAL(9,6) NULL,
  gps_long       DECIMAL(9,6) NULL,
  qr_code        VARCHAR(128) NOT NULL,
  PRIMARY KEY (fahrzeug_id),
  UNIQUE KEY uq_fahrzeuge_qr (qr_code),
  CONSTRAINT fk_fahrzeuge_anbieter
    FOREIGN KEY (anbieter_id) REFERENCES anbieter(anbieter_id),
  CONSTRAINT fk_fahrzeuge_typ
    FOREIGN KEY (fahrzeugtyp_id) REFERENCES fahrzeugtyp(fahrzeugtyp_id),
  CONSTRAINT chk_akku CHECK (akku_prozent <= 100)
) ENGINE=InnoDB;

CREATE TABLE zahlungsmittel (
  zahlungsmittel_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  benutzer_id       INT UNSIGNED NOT NULL,
  typ               VARCHAR(30)  NOT NULL,
  details           VARCHAR(255) NULL,
  PRIMARY KEY (zahlungsmittel_id),
  CONSTRAINT fk_zahlungsmittel_benutzer
    FOREIGN KEY (benutzer_id) REFERENCES benutzer(benutzer_id)
    ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE fahrt (
  fahrt_id    INT UNSIGNED NOT NULL AUTO_INCREMENT,
  fahrzeug_id INT UNSIGNED NOT NULL,
  benutzer_id INT UNSIGNED NOT NULL,
  startzeit   DATETIME NOT NULL,
  endzeit     DATETIME NULL,
  kilometer   DECIMAL(10,3) NOT NULL DEFAULT 0.000,
  preis       DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  PRIMARY KEY (fahrt_id),
  CONSTRAINT fk_fahrt_fahrzeug
    FOREIGN KEY (fahrzeug_id) REFERENCES fahrzeuge(fahrzeug_id),
  CONSTRAINT fk_fahrt_benutzer
    FOREIGN KEY (benutzer_id) REFERENCES benutzer(benutzer_id),
  CONSTRAINT chk_fahrt_zeiten CHECK (endzeit IS NULL OR endzeit >= startzeit),
  CONSTRAINT chk_fahrt_km CHECK (kilometer >= 0),
  CONSTRAINT chk_fahrt_preis CHECK (preis >= 0)
) ENGINE=InnoDB;

CREATE TABLE abrechnung (
  transaktion_id    INT UNSIGNED NOT NULL AUTO_INCREMENT,
  fahrt_id          INT UNSIGNED NOT NULL,
  zahlungsmittel_id INT UNSIGNED NOT NULL,
  betrag            DECIMAL(10,2) NOT NULL,
  zeitpunkt         DATETIME NOT NULL,
  PRIMARY KEY (transaktion_id),
  UNIQUE KEY uq_abrechnung_fahrt (fahrt_id),
  CONSTRAINT fk_abrechnung_fahrt
    FOREIGN KEY (fahrt_id) REFERENCES fahrt(fahrt_id),
  CONSTRAINT fk_abrechnung_zahlungsmittel
    FOREIGN KEY (zahlungsmittel_id) REFERENCES zahlungsmittel(zahlungsmittel_id),
  CONSTRAINT chk_abrechnung_betrag CHECK (betrag >= 0)
) ENGINE=InnoDB;

SET FOREIGN_KEY_CHECKS = 1;
