// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract SwarmChain {
    struct Record { uint256 nodeId; string dataHash; uint256 timestamp; }
    Record[] public records;

    event RecordAdded(uint256 indexed nodeId, string dataHash, uint256 timestamp);

    function addRecord(uint256 nodeId, string memory dataHash) public {
        records.push(Record(nodeId, dataHash, block.timestamp));
        emit RecordAdded(nodeId, dataHash, block.timestamp);
    }

    function getRecords() public view returns (uint256[] memory, string[] memory, uint256[] memory) {
        uint256 n = records.length;
        uint256[] memory ids = new uint256[](n);
        string[] memory hashes = new string[](n);
        uint256[] memory times = new uint256[](n);
        for (uint i = 0; i < n; i++) {
            ids[i] = records[i].nodeId;
            hashes[i] = records[i].dataHash;
            times[i] = records[i].timestamp;
        }
        return (ids, hashes, times);
    }
}
