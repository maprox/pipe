#!/usr/bin/php5
<?php

define('WORKING_DIR', __DIR__ . '/');

include WORKING_DIR . 'shell-common.php';

function is_ip($string)
{
	return preg_match('/^\d{1,3}((\.\d{1,3}){3}|(\.\d{1,3}){0,2}\.\*)$/', $string);
}

function incorrect_arguments()
{
	$file = basename(__FILE__);
	print "Usage: ./$file [{block|unblock|list} default=block]".
		" [valid ip-address] {tr203|tr206|tr600|...|all}\n";
	exit();
}

function getBanTrackers($name)
{
	if ($name == 'all')
	{
		return getAllTrackers();
	}

	return getTrackers(array($name));
}

function blockIp($ip, $tracker)
{
	$trackers = getBanTrackers($tracker);

	foreach ($trackers as $tracker => $port)
	{
		print "Blocking $ip from $tracker tracker... ";
		shell_exec("sudo iptables -t filter --append INPUT -p tcp -s $ip --dport $port -j REJECT > /dev/null 2>&1");
		print "[OK]\n";
	}
}

function unblockIp($ip, $tracker)
{
	$trackers = getBanTrackers($tracker);

	foreach ($trackers as $tracker => $port)
	{
		print "Allowing $ip to $tracker tracker... ";
		shell_exec("sudo iptables -t filter --delete INPUT -p tcp -s $ip --dport $port -j REJECT > /dev/null 2>&1");
		print "[OK]\n";
	}
}

function listTrackers($tracker)
{
	$trackers = getBanTrackers($tracker);

	foreach ($trackers as $tracker => $port)
	{
		$data = shell_exec("sudo iptables -t filter --list");
		print "Blocked IPs for tracker $tracker:\n";
		$data = explode("\n", $data);
		foreach ($data as $line)
		{
			if (preg_match('/REJECT\s+tcp[\s\-]+([\d\.]+).*dpt:' . $port . '/us', $line, $ip)) {
				print $ip[1] . "\n";
			}
		}
	}
}

// read input arguments
$params = arguments($argv);
$params = $params['input'];

if (empty($params[0]))
{
	incorrect_arguments();
}

if (is_ip($params[0]))
{
	array_unshift($params, 'block');
}

print "Pipe-server Ban tool v1.0.0\n";

switch ($params[0])
{
	case 'block':
		if (empty($params[1]) || empty($params[2]))
		{
			incorrect_arguments();
		}
		blockIp($params[1], $params[2]);
		break;
	case 'unblock':
		if (empty($params[1]) || empty($params[2]))
		{
			incorrect_arguments();
		}
		unblockIp($params[1], $params[2]);
		break;
	case 'list':
		if (empty($params[1]))
		{
			incorrect_arguments();
		}
		listTrackers($params[1]);
		break;
	default:
		incorrect_arguments();
}
