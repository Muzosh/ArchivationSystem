-- Create tables
use archivationsystem;
CREATE table ArchivedFiles(
	FileID int NOT NULL AUTO_INCREMENT UNIQUE,
	FileName NVARCHAR(255) NOT NULL,
	OwnerName NVARCHAR(255) NOT NULL,
	OriginalFilePath NVARCHAR(1024) NOT NULL,
	PackageStoragePath NVARCHAR (1024) NOT NULL,
	OriginFileHashSha512 BLOB NOT NULL,
	TimeOfFirstTS DATETIME NOT NULL,
	SigningCert BLOB NOT NULL,
	SignatureHashSha512 BLOB NOT NULL,
	Package0HashSha512 BLOB NOT NULL,
	ExpirationDateTS DATETIME NOT NULL,
	PRIMARY KEY(FileID),
	CONSTRAINT FN_O UNIQUE (FileName, OwnerName)
) ENGINE = InnoDB CHARSET = utf8;
CREATE table FilePackages(
	PackageID int NOT NULL AUTO_INCREMENT UNIQUE,
	ArchivedFileID int NOT NULL,
	TimeStampingAuthority NVARCHAR(255) NOT NULL,
	IssuingDate DATETIME NOT NULL,
	TsaCert BLOB NOT NULL,
	PackageHashSha512 BLOB NOT NULL,
	PRIMARY KEY (PackageID),
	FOREIGN KEY (ArchivedFileID) REFERENCES ArchivedFiles(FileID)
) ENGINE = InnoDB CHARSET = utf8;