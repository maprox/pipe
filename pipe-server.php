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
define('WORKING_DIR', "/var/observer/Server/trunk/");
# Sleep time for checking ports
define('SLEEP_TIME', 1); // seconds
define('MAX_WAIT_COUNT', 50); // seconds

/**
 * Arguments parsing
 * @param array $argv
 * @return array
 */
function arguments($argv) {
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
function getTrackers($names)
{
	$return = array();

	foreach ($names as $name)
	{
		$file = WORKING_DIR . "conf/serv-$name.conf";
		if (file_exists($file))
		{
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
 * Returns true if there is a server instance running
 * @param String $key Tracker key
 * @return Boolean
 */
function isProcessRunning($key)
{
	$mask = "[p]ython.*serv-$key";

	$output = shell_exec("sudo pgrep -f $mask 2>&1");

	return $output != NULL;
}

/**
 * Kills process by mask
 * @param string $key
 */
function killProcess($key)
{
	$mask = "[p]ython.*serv-$key";

	print "Stopping... ";
	$command = "sudo pkill -f $mask 2>&1";
	$output = shell_exec($command);
	print_r($output);
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
function startProcess($trackers)
{
	foreach ($trackers as $key => $port)
	{
		print "Starting process for tracker $key... ";
		startInBackground(WORKING_DIR . "pipe-start $key " . WORKING_DIR);
		print "[OK]\n";
	}
}

/**
 * Service start
 */
function serviceStart($input)
{
	if (empty($input))
	{
		$trackers = getAllTrackers();
	}
	else
	{
		$trackers = getTrackers($input);
	}

	print "Ports check\n";
	$silentMode = false;

	foreach ($trackers as $key => $port)
	{
		// check if process already running
		if (isProcessRunning($key))
		{
			if (!$silentMode)
			{
				print "Pipe-process for protocol $key is already running. Restart? [Y/n]:";
				if (!getUserConfirm())
				{
					unset($trackers[$key]);
					continue;
				}
			}
			killProcess($key);
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
			if (!forceOpenPorts())
			{
				print "Failed to free port $port";
				unset($trackers[$key]);
				continue;
			}
		}
	}

	startProcess($trackers);
}

/**
 * Kills pipe-server processes
 */
function serviceStop($input)
{
	if (empty($input))
	{
		$trackers = getAllTrackers();
	}
	else
	{
		$trackers = getTrackers($input);
	}

	foreach ($trackers as $key => $port)
	{
		killProcess($key);
	}

}

/**
 * Tests if process already running
 */
function serviceTest($input)
{
	if (empty($input))
	{
		$trackers = getAllTrackers();
	}
	else
	{
		$trackers = getTrackers($input);
	}

	foreach ($trackers as $key => $port)
	{
		if (isProcessRunning($key))
		{
			print "Listener for protocol $key is running\n";
		}
		else
		{
			print "Listener for protocol $key is down\n";
		}
	}
}

print "Pipe-server Starter v1.0.2\n";

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
		serviceStart($params['input']);
		break;
	case 'stop':
		serviceStop($params['input']);
		break;
	case 'restart':
	case 'force-reload':
	case 'reload':
		serviceStop($params['input']);
		serviceStart($params['input']);
		break;
	case 'status':
		serviceTest($params['input']);
		break;
	default:
		print "Usage: $0 {start|stop|restart|reload|force-reload|status}\n";
}
