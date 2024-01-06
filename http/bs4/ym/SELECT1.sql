-- AVGOSU list sample 1
SELECT
	A.film_id, A.file_size, A.avgosu_date, A.title
	, CONCAT('https://avgosu5.com/torrent/etc/', A.avgosu_board_no, '.html') AS detail_url
	, CONCAT('magnet:?xt=urn:btih:', HEX(A.magnet_info)) as magnet_addr
	, fn_has_yamoon_script(A.film_id) AS ym
FROM `AVGOSU` AS A
WHERE 1 = 1
	AND ( (fn_has_yamoon_script(A.film_id) > 0) OR (fn_has_hellven_script(A.film_id) > 0) )
	AND resolution = 'F'
ORDER BY A.avgosu_no DESC
LIMIT 0, 30;
