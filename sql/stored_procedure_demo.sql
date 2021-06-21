
CREATE OR REPLACE TABLE PRODUCT
(
	product_no		INT NOT NULL AUTO_INCREMENT
	, product_name	VARCHAR(250) NOT NULL
	, product_uuid	VARCHAR(40) NOT NULL
	, serial_code	CHAR(8) NOT NULL
	
	, PRIMARY KEY ( product_no )
);


DELIMITER $$

CREATE OR REPLACE PROCEDURE sp_generate_product( IN p_need_count INT )
	LANGUAGE SQL
	NOT DETERMINISTIC
	CONTAINS SQL
	SQL SECURITY DEFINER
	COMMENT '입력한 개수만큼 PRODUCT를 생성한 후, 이를 반환합니다.'
BEGIN


DECLARE v_uuid VARCHAR(60);
DECLARE v_crc32 VARCHAR(8);
DECLARE v_product_no INT;


DECLARE EXIT HANDLER FOR SQLEXCEPTION
BEGIN
	ROLLBACK;
	DROP TABLE IF EXISTS T_PRODUCT_LIST;
END;


CREATE OR REPLACE TEMPORARY TABLE T_PRODUCT_LIST
(
	product_no	INT NOT NULL
);


START TRANSACTION;


FOR v_index IN 1..p_need_count DO

	SET v_uuid = UUID();
	SET v_crc32 = HEX(CRC32(v_uuid));

	INSERT INTO PRODUCT ( product_name, product_uuid, serial_code )
	VALUES ('product', v_uuid, v_crc32);
	
	SET v_product_no = LAST_INSERT_ID();
	INSERT INTO T_PRODUCT_LIST VALUES ( v_product_no );

END FOR;

COMMIT;

SELECT
	L.product_no, P.product_name, P.product_uuid, P.serial_code
FROM T_PRODUCT_LIST AS L
	INNER JOIN PRODUCT AS P ON P.product_no = L.product_no
ORDER BY 1;


DROP TABLE IF EXISTS T_PRODUCT_LIST;


END$$

DELIMITER ;


CALL sp_generate_product(3);
