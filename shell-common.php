<?php

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
		preg_match('/conf\/serv-(.*)\.conf/ui', $file, $key);
		$name = $key[1];

		$return[$name] = readTrackerConfig($name);
	}

	return array_filter($return);
}

/**
 * Parses conf files of given protocols and returns array
 * @return array
 */
function getTrackers($names, $port = false)
{
	$return = array();
	foreach ($names as $name)
	{
		$return[$name] = readTrackerConfig($name, $port);
	}

	return array_filter($return);
}

function readTrackerConfig($name, $port = false)
{
	$file = WORKING_DIR . "conf/serv-$name.conf";
	if (!file_exists($file))
	{
		return false;
	}

	$return = array(
		'pipeconf' => getPipeConf($name)
	);
	$return['config'] = readIni(WORKING_DIR . $return['pipeconf'], 'urlconfig');
	$return['host'] = readIni(WORKING_DIR . $return['pipeconf'], 'host');

	if ($port)
	{
		$return['port'] = $port;
	}
	else
	{
		$return['port'] = readIni($file, 'port');
	}

	return $return['port'] ? $return : false;
}

function readIni($file, $option)
{
	$data = file($file);

	foreach ($data as $line)
	{
		if (preg_match('/^' . $option . '=(.*)/', trim($line), $config))
		{
			return $config[1];
		}
	}

	return null;
}

/**
 * Finds pipe configuration file
 */
function getPipeConf($name)
{
	$file = WORKING_DIR . "conf/pipe-$name.conf";
	if (file_exists($file)) {
		return "conf/pipe-$name.conf";
	}

	$file = WORKING_DIR . "conf/pipe-default.conf";
	if (file_exists($file)) {
		return "conf/pipe-default.conf";
	}

	return "conf/pipe.conf";
}

/**
 * Starts command in background
 * @param string $command
 */
function startInBackground($command)
{
	shell_exec("nohup $command > /dev/null 2>&1");
}
