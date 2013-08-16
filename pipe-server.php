#!/usr/bin/php5
<?php /*
### BEGIN INIT INFO
# Provides:          pipe-server
# Required-Start:    $local_fs $remote_fs $syslog $network
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
# Sleep time for checking ports
define('SLEEP_TIME', 1); // seconds
define('MAX_WAIT_COUNT', 50); // seconds
define('DEFAULT_FLAG', 'default');

include WORKING_DIR . 'shell-common.php';

/**
 * Test port availability
 * @param int $port
 * @return bool
 */
function isPortOpen($port)
{
	$output = shell_exec("sudo fuser -v $port/tcp 2>&1");
	return $output == NULL;
}

/**
 * Function force-opens needed port, killing occupying processes
 * @param int $port
 * @return bool True if all ports are closed
 */
function forceOpenPort($port)
{
	$counter = MAX_WAIT_COUNT;
	print("Closing port $port");
	while (!isPortOpen($port)) {
		shell_exec("sudo fuser -vk $port/tcp 2>&1");
		print(".");
		if ($counter-- < 1) {
			print("[FAIL]\n");
			return false;
		}
		sleep(SLEEP_TIME);
	}
	print("[OK]\n");
	return true;
}

/**
 * Returns user confirmation
 * @param bool $default Returning value if user press only <enter> key
 * @return bool
 */
function getUserConfirm($default = true)
{
	$handle = fopen("php://stdin", "r");
	$line = strtolower(trim(fgets($handle)));
	if (strlen($line) === 0) {
		return $default;
	}
	return ($line === 'y');
}

/**
 * Builds process identifier
 * @param string $key
 * @param string $flag
 * @return string
 */
function getMask($key, $flag)
{
	return md5($key . " " . $flag);
}

/**
 * Returns true if there is a server instance running
 * @param String $key Tracker key
 * @return Boolean
 */
function isProcessRunning($mask)
{
	$mask = "[p]ython.*pipe_process_mask=$mask";
	$output = shell_exec("sudo pgrep -f $mask 2>&1");
	return $output != NULL;
}

/**
 * Kills process by mask
 * @param string $mask
 */
function killProcess($mask)
{
	$mask = "[p]ython.*pipe_process_mask=$mask";

	print("Stopping... ");
	$command = "sudo pkill -f $mask 2>&1";
	$output = shell_exec($command);
	print_r($output);

	print("[OK]\n");
}

/**
 * Kills all processess, regardless of flags
 */
function killAll()
{
	$mask = "[p]ython.*pipe_process_mask=";

	print("Stopping all processes... ");
	$command = "sudo pkill -f $mask 2>&1";
	$output = shell_exec($command);
	print_r($output);

	print("[OK]\n");
}

/**
 * Start process
 */
function startProcess($trackers, $flag)
{
	foreach ($trackers as $key => $config) {
		$mask = getMask($key, $flag);
		print("Starting [$key] protocol process... ");
		startInBackground("sudo -u pipe " . WORKING_DIR .
			"pipe-start $key $mask $config[port] $config[pipeconf] " . WORKING_DIR);
		print("[OK]\n");
	}
}

/**
 * Service start
 */
function serviceStart($params)
{
	if (empty($params['input'])) {
		$trackers = getAllTrackers();
	} else {
		$trackers = getTrackers($params['input'], $params['port']);
	}

	print("Ports check\n");
	$silentMode = false;

	foreach ($trackers as $key => $config) {
		$mask = getMask($key, $params['flag']);
		// check if process already running
		if (isProcessRunning($mask)) {
			if (!$silentMode) {
				print("Pipe-process for protocol $key with $params[flag] flag " .
					" is already running. Restart? [Y/n]:");
				if (!getUserConfirm()) {
					unset($trackers[$key]);
					continue;
				}
			}
			killProcess($mask);
		}

		// check for opened ports
		if ($config['port'] && !isPortOpen($config['port'])) {
			print("Port $config[port] are busy by someone else.\n");
			if (!$silentMode) {
				print("Free port $config[port] forcefully? [Y/n]");
				if (!getUserConfirm()) {
					unset($trackers[$key]);
					continue;
				}
			}
			if (!forceOpenPort($config['port'])) {
				print("Failed to free port $config[port]");
				unset($trackers[$key]);
				continue;
			}
		}
	}

	startProcess($trackers, $params['flag']);
}

/**
 * Kills pipe-server processes
 */
function serviceStop($params)
{
	if ($params['stop'] == 'all') {
		killAll();
	} else {
		if (empty($params['input'])) {
			$trackers = getAllTrackers();
		} else {
			$trackers = getTrackers($params['input'], $params['port']);
		}
		foreach ($trackers as $key => $devNull) {
			$mask = getMask($key, $params['flag']);
			killProcess($mask);
		}
	}
}

/**
 * Tests if process already running
 */
function serviceTest($params)
{
	if (empty($params['input'])) {
		$trackers = getAllTrackers();
	} else {
		$trackers = getTrackers($params['input'], $params['port']);
	}

	foreach ($trackers as $key => $devNull) {
		$mask = getMask($key, $params['flag']);
		$status = isProcessRunning($mask) ? "running" : "down";
		print("Listener for protocol $key with $params[flag] flag is $status\n");
	}
}

/**
 * Performs installation of service
 */
function doInstall()
{
	shell_exec('sudo ln -s ' . __FILE__ . ' /etc/init.d/pipe-server');
	shell_exec('sudo chmod +x ' . __FILE__);
	shell_exec('sudo update-rc.d pipe-server defaults');
	print("Installation complete\n");
}

print("Pipe-server Starter v2.1\n");

// read input arguments
$command = '';
$params = arguments($argv);
if (is_array($params['input']) && !empty($params['input'][0])) {
	$command = array_shift($params['input']);
}
if (!empty($params['f'])) {
	$params['flag'] = $params['f'];
}
if (!empty($params['p'])) {
	$params['port'] = $params['p'];
}
if (!empty($params['s'])) {
	$params['stop'] = $params['s'];
}

$params['flag'] = empty($params['flag']) ? DEFAULT_FLAG : $params['flag'];
$params['port'] = empty($params['port']) ? false : $params['port'];
$params['stop'] = empty($params['stop']) ? false : $params['stop'];

switch ($command)
{
	case 'install':
		doInstall();
		break;
	case 'start':
		serviceStart($params);
		break;
	case 'stop':
		serviceStop($params);
		break;
	case 'restart':
	case 'force-reload':
	case 'reload':
		serviceStop($params);
		serviceStart($params);
		break;
	case 'status':
		serviceTest($params);
		break;
	default:
		$file = basename(__FILE__, '.php');
		print("Usage: service $file " .
			"{start|stop|restart|reload|force-reload|status}" .
			" [{--stop|-s}=all] [{--flag|-f}=%FLAG%] " .
			"[{--port|-p}=%PORT%] [%TRACKER_1%] [%TRACKER_2%] " .
			"... [%TRACKER_N%]\n" .
			"Install: php " . $params['name'] . " install\n");
}
