QUERY_ALL_COLUMNS_ON_FILEID_ARCHIVED_FILES = (
    "select * from ArchivedFiles where FileID = {};"
)


QUERY_FILEID_ON_FILENAME_OWNER_ARCHIVED_FILES = (
    "select FileID from ArchivedFiles "
    "where FileName = '{}' and OwnerName like '{}';"
)

QUERY_ALL_COLUMNS_ON_FILEID_FILE_PACKAGES = (
    "select * from FilePackages "
    "where ArchivedFileID = '{}' order by IssuingDate desc;"
)

QUERY_ALL_COLUMNS_ON_FILEID_FILE_PACKAGES_TOP1 = (
    "select * from FilePackages "
    "where ArchivedFileID = {} order by IssuingDate desc "
    "limit 1;"
)

QUERY_UPDATE_EXPIRATION_DATE_ARCHIVED_FILES = (
    "UPDATE ArchivedFiles SET ExpirationDateTS = '{}' WHERE FileID = {};"
)

QUERY_INSERT_INTO_ARCHIVED_FILES = (
    "INSERT into ArchivedFiles(FileName, OwnerName, OriginalFilePath,"
    " PackageStoragePath, OriginFileHashSha512, TimeOfFirstTS, SigningCert,"
    " SignatureHashSha512, Package0HashSha512, ExpirationDateTS) Values('{}',"
    " '{}', '{}', '{}', {}, '{}', {}, {}, {},'{}');"
)

QUERY_INSERT_INTO_FILE_PACKAGES = (
    "INSERT into FilePackages(ArchivedFileID, TimeStampingAuthority,"
    " IssuingDate, TsaCert, PackageHashSha512) Values( '{}', '{}', '{}', {},"
    " {});"
)


QUERY_SELECT_FILEID = "select FileID from ArchivedFiles"
