QUERY_ALL_COLUMNS_ON_FILEID_ARCHIVATED_FILES = (
    "select * from ArchivatedFiles "
    "where FileID = {};"
)


QUERY_FILEID_ON_FILENAME_OWNER_ARCHIVATED_FILES = (
    "select FileID from ArchivatedFiles "
    "where FileName = '{}' and OwnerName like '{}';"
)

QUERY_ALL_COLUMNS_ON_FILEID_FILE_PACKAGES = (
    "select * from FilePackages "
    "where ArchivatedFileID = '{}' order by IssuingDate desc;"
)

QUERY_ALL_COLUMNS_ON_FILEID_FILE_PACKAGES_TOP1 = (
    "select * from FilePackages "
    "where ArchivatedFileID = {} order by IssuingDate desc "
    "limit 1;"
)

QUERY_UPDATE_EXPIRATION_DATE_ARCHIVATED_FILES = (
    "UPDATE ArchivatedFiles SET ExpirationDateTS = '{}' WHERE FileID = {};"
)

QUERY_INSRET_INTO_ARCHIVATED_FILES = (
    "INSERT into ArchivatedFiles(FileName, OwnerName, OriginalFilePath, PackageStoragePath, OriginFileHashSha512, TimeOfFirstTS, SigningCert, SignatureHashSha512, Package0HashSha512, ExpirationDateTS) "
    "Values('{}', '{}', '{}', '{}', {}, '{}', {}, {}, {},'{}');"
)

QUERY_INSRET_INTO_FILE_PACKAGES = (
    "INSERT into FilePackages(ArchivatedFileID, TimeStampingAuthority, IssuingDate, TsaCert, PackageHashSha512) "
    "Values( '{}', '{}', '{}', {}, {});"
)



QUERY_SELECT_FILEID = (
    "select FileID from ArchivatedFiles"
)