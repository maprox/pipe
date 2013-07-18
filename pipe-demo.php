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
 * Performs installation of service
 */
function doInstall()
{
	if (!isLinux()) {
		print "Install is not supported on windows!";
		die();
	}
	shell_exec('sudo ln -s ' . __FILE__ . ' /etc/init.d/pipe-demo');
	shell_exec('sudo chmod +x ' . __FILE__);
	shell_exec('sudo update-rc.d pipe-demo defaults');
	print "Installation complete\n";
}

/**
 * Service start
 */
function serviceStart($debug)
{
		print "Starting demo-server... ";
		if ($debug) {
			$params = '-d navitech -p conf/pipe-debug.conf';
		} else {
			$params = '';
		}
		if (isLinux()) {
			exec("sudo -u pipe python3 demo.py $params >/dev/null &");
		} else {
			$shell = new COM("WScript.Shell");
			$shell->run("python3 demo.py $params", 0, false);
		}
		print "[OK]\n";
}

/**
 * Kills pipe-server processes
 */
function serviceStop($debug)
{
	if ($debug) {
		$mask = "[p]ython.*demo\.py.*debug";
	} else {
		$mask = "[p]ython.*demo\.py\s*$";
	}

	print "Stopping... ";
	$command = "sudo pkill -f $mask 2>&1";
	if (!isLinux()) {
		$command = "wmic Path win32_process Where " .
			"\"CommandLine Like '%python% demo.py%'\" Call Terminate";
	}
	$output = shell_exec($command);
	print_r($output);
	print "[OK]\n";
}

/**
 * Tests if process already running
 */
function serviceTest()
{
	if (!isLinux()) { return; }
	$mask = "[p]ython.*demo\.py";
	$output = shell_exec("sudo pgrep -f $mask 2>&1");
	if ($output != NULL) {
		print "Democlient is running\n";
	} else {
		print "Democlient is down\n";
	}
}

print "Pipe-demo Starter v2.0.0\n";

// read input arguments
$command = '';
$params = arguments($argv);
if (is_array($params['input']) && !empty($params['input'][0])) {
	$command = array_shift($params['input']);
}
if (is_array($params['input']) && !empty($params['input'][0])) {
	$debug = ($params['input'][0] == 'debug');
} else {
	$debug = false;
}

switch ($command)
{
	case 'install':
		doInstall();
		break;	
	case 'start':
		serviceStart($debug);
		break;
	case 'stop':
		serviceStop($debug);
		break;
	case 'restart':
	case 'force-reload':
	case 'reload':
		serviceStop($debug);
		serviceStart($debug);
		break;
	case 'status':
		serviceTest($debug);
		break;
	default:
		$file = basename(__FILE__, '.php');
		print "Usage: service $file {start|stop|restart|reload|force-reload|status} {debug|normal}\n" .
			"Install: php " . $params['name'] . " install\n";
}
