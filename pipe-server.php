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

/**
 * Arguments parsing
 * @param array $argv
 * @return array
 */
function arguments($argv)
{
	$_ARG = array('input' => array());
	// First param is this scripts name. Not needed.
	array_shift($argv);
	foreach ($argv as $arg)
	{
		if (preg_match('#^-{1,2}([a-zA-Z0-9]*)=?(.*)$#', $arg, $matches))
		{
			$key = $matches[1];
			switch ($matches[2])
			{
				case '':
				case 'true':
					$arg = true;
					break;
				case 'false':
					$arg = false;
					break;
				default:
					$arg = $matches[2];
			}
			$_ARG[$key] = $arg;
		}
		else
		{
			$_ARG['input'][] = $arg;
		}
	}

	return $_ARG;
}

/**
 * Parses all conf files and returns array of protocols
 * @return array
 */
function getAllTrackers()
{
	$files = glob(WORKING_DIR . "conf/serv-*.conf");
	$return = array();

	foreach ($files as $file)
	{
		$key = array();
		preg_match('/conf\/serv-(.*)\.conf/ui', $file, $key);

		$data = file($file);

		foreach ($data as $line)
		{
			if (preg_match('/^port=(\d+)/', $line, $port))
			{
				$return[$key[1]] = $port[1];
				break;
			}
		}
	}

	return $return;
}

/**
 * Parses conf files of given protocols and returns array
 * @return array
 */
function getTrackers($names, $port)
{
	$return = array();
	foreach ($names as $name)
	{
		$file = WORKING_DIR . "conf/serv-$name.conf";
		if (file_exists($file))
		{
			if ($port && count($names) == 1)
			{
				$return[$name] = $port;
				continue;
			}

			$data = file($file);

			foreach ($data as $line)
			{
				if (preg_match('/^port=(\d+)/', $line, $port))
				{
					$return[$name] = $port[1];
					break;
				}
			}
		}
	}

	return $return;
}

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
	print "Closing port $port";
	while (!isPortOpen($port))
	{
		shell_exec("sudo fuser -vk $port/tcp 2>&1");
		print ".";
		if ($counter-- < 1)
		{
			print "[FAIL]\n";
			return false;
		}
		sleep(SLEEP_TIME);
	}
	print "[OK]\n";
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
	if (strlen($line) === 0)
		return $default;
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
	$mask = "[p]ython.*serv-$mask";

	$output = shell_exec("sudo pgrep -f $mask 2>&1");

	return $output != NULL;
}

/**
 * Kills process by mask
 * @param string $mask
 */
function killProcess($mask)
{
	$mask = "[p]ython.*pipe_server_mask=$mask";

	print "Stopping... ";
	$command = "sudo pkill -f $mask 2>&1";
	$output = shell_exec($command);
	print_r($output);
	print "[OK]\n";
}

/**
 * Kills all processess, regardless of flags
 */
function killAll()
{
	$mask = "[p]ython.*pipe_server_mask=";

	print "Stopping all processes... ";
	$command = "sudo pkill -f $mask 2>&1";
	$output = shell_exec($command);
	print_r($output);

	// Чтобы остановить то, что уже было запущено в прошлой версии. Убрать.
	$command = "sudo pkill -f [p]ython.*serv 2>&1";
	$output = shell_exec($command);

	print "[OK]\n";
}

/**
 * Starts command in background
 * @param string $command
 */
function startInBackground($command)
{
	shell_exec("nohup $command > /dev/null 2>&1");
}

/**
 * Start process
 */
function startProcess($trackers, $flag)
{
	foreach ($trackers as $key => $port)
	{
		$mask = getMask($key, $flag);

		print "Starting process for tracker $key... ";
		startInBackground(WORKING_DIR . "pipe-start $key $mask $port " . WORKING_DIR);
		print "[OK]\n";
	}
}

/**
 * Service start
 */
function serviceStart($params)
{
	if (empty($params['input']))
	{
		$trackers = getAllTrackers();
	}
	else
	{
		$trackers = getTrackers($params['input'], $params['port']);
	}

	print "Ports check\n";
	$silentMode = false;

	foreach ($trackers as $key => $port)
	{
		$mask = getMask($key, $params['flag']);
		// check if process already running
		if (isProcessRunning($mask))
		{
			if (!$silentMode)
			{
				print "Pipe-process for protocol $key with $params[flag] flag is already running. Restart? [Y/n]:";
				if (!getUserConfirm())
				{
					unset($trackers[$key]);
					continue;
				}
			}
			killProcess($mask);
		}

		// check for opened ports
		if (!isPortOpen($port))
		{
			print "Port $port are busy by someone else.\n";
			if (!$silentMode)
			{
				print "Free port $port forcefully? [Y/n]";
				if (!getUserConfirm())
				{
					unset($trackers[$key]);
					continue;
				}
			}
			if (!forceOpenPort($port))
			{
				print "Failed to free port $port";
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
	if ($params['stop'] == 'all')
	{
		killAll();
		return;
	}

	if (empty($params['input']))
	{
		$trackers = getAllTrackers();
	}
	else
	{
		$trackers = getTrackers($params['input'], $params['port']);
	}

	foreach ($trackers as $key => $devNull)
	{
		$mask = getMask($key, $params['flag']);
		killProcess($mask);
	}

}

/**
 * Tests if process already running
 */
function serviceTest($params)
{
	if (empty($params['input']))
	{
		$trackers = getAllTrackers();
	}
	else
	{
		$trackers = getTrackers($params['input'], $params['port']);
	}

	foreach ($trackers as $key => $devNull)
	{
		$mask = getMask($key, $params['flag']);
		if (isProcessRunning($mask))
		{
			print "Listener for protocol $key with $params[flag] flag is running\n";
		}
		else
		{
			print "Listener for protocol $key with $params[flag] flag is down\n";
		}
	}
}

print "Pipe-server Starter v1.0.4\n";

// read input arguments
$command = '';
$params = arguments($argv);
if (is_array($params['input']) && !empty($params['input'][0]))
{
	$command = array_shift($params['input']);
}
if (!empty($params['f']))
{
	$params['flag'] = $params['f'];
}
if (!empty($params['p']))
{
	$params['port'] = $params['p'];
}
if (!empty($params['s']))
{
	$params['stop'] = $params['s'];
}

$params['flag'] = empty($params['flag']) ? DEFAULT_FLAG : $params['flag'];
$params['port'] = empty($params['port']) ? false : $params['port'];
$params['stop'] = empty($params['stop']) ? false : $params['stop'];

switch ($command)
{
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
		print "Usage: service $file {start|stop|restart|reload|force-reload|status}".
			" [{--stop|-s}=all] [{--flag|-f}=%FLAG%] [{--port|-p}=%PORT%] [%TRACKER_1%] [%TRACKER_2%] ... [%TRACKER_N%]\n";
}
