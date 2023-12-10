-- DROP TABLE IF EXISTS `SCRIPTS_YAMOON`
CREATE TABLE IF NOT EXISTS `SCRIPTS_YAMOON`
(
	`script_yamoon_no`		INT NOT NULL AUTO_INCREMENT COMMENT '야문 자막 파일 고유번호'
	, `yamoon_board_no`		INT NOT NULL COMMENT '야문 자막 게시판의 번호'
	, `uploader`			VARCHAR(50) NOT NULL COMMENT '자막 올린이' COLLATE 'utf8mb4_unicode_ci'
	, `board_date`			DATETIME NOT NULL COMMENT '자막 등록 날짜'
	, `script_name`			VARCHAR(200) NOT NULL COMMENT '자막 파일 이름' COLLATE 'utf8mb4_unicode_ci'
	, `file_size`			INT NULL COMMENT '스크립트 파일 크기'
	, `script_path`			VARCHAR(100) NULL COMMENT '자막 파일 저장 경로' COLLATE 'utf8mb4_unicode_ci'
	, `film_id`				VARCHAR(50) NULL COMMENT '작품의 품번 (FK: FILM.film_id)'
	, `film_no`				INT NULL COMMENT '영상 고유 번호 (FK: FILM.film_no)'
	, `reg_date`			DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP() COMMENT '정보 등록시각'

	, PRIMARY KEY (`script_yamoon_no`) USING BTREE
	, UNIQUE INDEX `UK_FILM_ID_FILE_SIZE` (`yamoon_board_no`, `script_name`) USING BTREE
	, INDEX `IX_FILM_ID` ( `film_id` ) USING BTREE
)
COMMENT='야문 자막 정보 관리 테이블'
COLLATE='utf8mb4_unicode_ci'
ENGINE=InnoDB
;

/*
ALTER TABLE `SCRIPTS_YAMOON`
	ADD INDEX `IX_FILM_ID` ( `film_id` ) USING BTREE;
*/