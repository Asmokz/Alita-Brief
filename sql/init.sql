CREATE DATABASE IF NOT EXISTS alita_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE alita_db;

-- Table portfolio
CREATE TABLE IF NOT EXISTS portfolio (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ticker VARCHAR(20) NOT NULL,
    nom VARCHAR(100) NOT NULL,
    prix_achat DECIMAL(10,2) NOT NULL,
    quantite INT NOT NULL,
    date_achat DATETIME NOT NULL,
    actif BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_ticker (ticker),
    INDEX idx_actif (actif)
) ENGINE=InnoDB;

-- Table historique transactions
CREATE TABLE IF NOT EXISTS transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    portfolio_id INT,
    type_transaction ENUM('ACHAT', 'VENTE', 'MODIFICATION') NOT NULL,
    ticker VARCHAR(20) NOT NULL,
    prix DECIMAL(10,2),
    quantite INT,
    date_transaction DATETIME NOT NULL,
    note TEXT,
    FOREIGN KEY (portfolio_id) REFERENCES portfolio(id) ON DELETE SET NULL,
    INDEX idx_date (date_transaction)
) ENGINE=InnoDB;

-- Table configuration
CREATE TABLE IF NOT EXISTS config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cle VARCHAR(50) UNIQUE NOT NULL,
    valeur TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Valeurs par défaut
INSERT INTO config (cle, valeur) VALUES
('meteo_ville', 'Marseille'),
('briefing_heure', '07:30'),
('moto_seuil_vent', '20'),
('moto_seuil_pluie', '50');

-- Table cache API
CREATE TABLE IF NOT EXISTS api_cache (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cache_key VARCHAR(255) UNIQUE NOT NULL,
    data JSON NOT NULL,
    expires_at DATETIME NOT NULL,
    INDEX idx_expires (expires_at)
) ENGINE=InnoDB;

-- Table logs briefings
CREATE TABLE IF NOT EXISTS briefings_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date_envoi DATETIME NOT NULL,
    contenu TEXT,
    statut ENUM('SUCCESS', 'ERREUR') NOT NULL,
    message_erreur TEXT,
    INDEX idx_date (date_envoi)
) ENGINE=InnoDB;

-- Données de test portfolio
INSERT INTO portfolio (ticker, nom, prix_achat, quantite, date_achat) VALUES
('AIR.PA', 'Airbus', 145.20, 10, NOW()),
('BNP.PA', 'BNP Paribas', 58.50, 20, NOW()),
('SU.PA', 'Schneider Electric', 180.00, 5, NOW());

INSERT INTO transactions (portfolio_id, type_transaction, ticker, prix, quantite, date_transaction, note) VALUES
(1, 'ACHAT', 'AIR.PA', 145.20, 10, NOW(), 'Achat initial'),
(2, 'ACHAT', 'BNP.PA', 58.50, 20, NOW(), 'Achat initial'),
(3, 'ACHAT', 'SU.PA', 180.00, 5, NOW(), 'Achat initial');
