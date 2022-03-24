add jar ${SAMPLE}/libs/jsonserde.jar ;

drop table logs ;
create external table logs (requestBeginTime string, requestEndTime string, hostname string)
  partitioned by (dt string)
  row format
    serde 'org.openx.data.jsonserde.JsonSerDe'
    with serdeproperties ( 'paths'='requestBeginTime, requestEndTime, hostname' )
  location '${SAMPLE}/tables/impressions' ;

--alter table logs recover partitions ;
msck repair table logs;
show partitions logs ;

drop table local_metrics ;
create table local_metrics (requestTime double, hostname string) ;

from logs
  insert overwrite table local_metrics
    select ((cast(requestEndTime as bigint)) - (cast(requestBeginTime as bigint)) / 1000.0) as requestTime, hostname
      where dt = '${DATE}'
;

from local_metrics
  select transform ( '${DATE}', max(requestTime), min(requestTime), avg(requestTime), 'ALL' )
    using '${SAMPLE}/libs/upload-to-simple-db hostmetrics metrics date,hostname date tmax tmin tavg hostname'
    as (output string)
;

from local_metrics
  select transform ( '${DATE}', max(requestTime), min(requestTime), avg(requestTime), hostname )
    using '${SAMPLE}/libs/upload-to-simple-db hostmetrics metrics date,hostname date tmax tmin tavg hostname'
    as (output string)
  group by hostname
;
