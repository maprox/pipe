#!/usr/bin/php5
<?php /*
### BEGIN INIT INFO
# Provides:          pipe-demo
# Required-Start:    $pipe-server $local_fs $remote_fs $syslog $network
# Required-Stop:     $local_fs $remote_fs $syslog $network
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# X-Interactive:     true
# Short-Description: Daemon for running packet listeners
# Description:       Daemon for running packet listeners
### END INIT INFO
*/

/**
 * Config
 */
define('WORKING_DIR', __DIR__ . '/');

include WORKING_DIR . 'shell-common.php';

/**
 * Service start
 */
function serviceStart()
{
		print "Starting demo-server... ";
		$dir = WORKING_DIR . 'democlient/';
		exec("cd $dir && sudo -u pipe python send2.py -p ../conf/pipe-default.conf >/dev/null &");
		print "[OK]\n";
}

/**
 * Kills pipe-server processes
 */
function serviceStop()
{
	$mask = "[p]ython.*send2\.py";

	print "Stopping... ";
	$command = "sudo pkill -f $mask 2>&1";
	$output = shell_exec($command);
	print_r($output);
	print "[OK]\n";
}

/**
 * Tests if process already running
 */
function serviceTest()
{
	$mask = "[p]ython.*send2\.py";

	$output = shell_exec("sudo pgrep -f $mask 2>&1");

	if ($output != NULL)
	{
		print "Democlient is running\n";
	}
	else
	{
		print "Democlient is down\n";
	}
}

print "Pipe-demo Starter v1.0.0\n";

// read input arguments
$command = '';
$params = arguments($argv);
if (is_array($params['input']) && !empty($params['input'][0]))
{
	$command = array_shift($params['input']);
}

switch ($command)
{
	case 'start':
		serviceStart();
		break;
	case 'stop':
		serviceStop();
		break;
	case 'restart':
	case 'force-reload':
	case 'reload':
		serviceStop();
		serviceStart();
		break;
	case 'status':
		serviceTest();
		break;
	default:
		$file = basename(__FILE__, '.php');
		print "Usage: service $file {start|stop|restart|reload|force-reload|status}\n";
}
