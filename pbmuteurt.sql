-- phpMyAdmin SQL Dump
-- version 3.3.10deb1
-- http://www.phpmyadmin.net
--
-- Serveur: localhost
-- Généré le : Mer 22 Mars 2012 à 12:24
-- Version du serveur: 5.1.54
-- Version de PHP: 5.3.5-1ubuntu7.2

SET SQL_MODE="NO_AUTO_VALUE_ON_ZERO";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;

--
-- Base de données: `b3`
--

-- --------------------------------------------------------

--
-- Structure de la table `pbmuteurt`
--

CREATE TABLE IF NOT EXISTS `pbmuteurt` (
  `client_id` int(10) NOT NULL,
  `raison` varchar(132) NOT NULL,
  `admin` int(10) NOT NULL,
  `datedebut` int(11) NOT NULL,
  `datefin` int(11) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

--
-- Contenu de la table `pbmuteurt`
--

