# Problem A: Walk the Line

There’s an old, narrow bridge that a group of N travelers wish to cross during the night. The bridge can only support the weight of at most 2 people at a time. The travelers must stay together and use the group’s only flashlight while on the bridge. Each traveler i can cross the bridge in Si seconds alone.

Thankfully, the group has a very lightweight wheelbarrow. There are two possible scenarios for crossing:

	1.	Traveler i can cross the bridge alone in Si seconds, optionally bringing the wheelbarrow.
	2.	Two travelers i and j can both cross together in Si seconds if traveler j rides in the wheelbarrow pushed by traveler i.

In both cases, any group crossing the bridge must bring the flashlight. The flashlight can be returned to the initial side by the same rules mentioned above. The task is to determine if there is a strategy for all travelers to cross the bridge within K seconds.

## Constraints

	•	1 ≤ T ≤ 95 (Number of test cases)
	•	1 ≤ N ≤ 1,000 (Number of travelers)
	•	1 ≤ Si, K ≤ 1,000,000,000 (Time taken by each traveler and maximum allowed time)

## Input Format

	•	The input begins with an integer T, the number of test cases.
	•	Each test case starts with a line containing two integers N and K.
	•	The next N lines contain one integer each, representing the time Si it takes for the i-th traveler to cross the bridge alone.

## Output Format

For each test case, print Case #i: YES if the travelers can all cross the bridge within K seconds, or Case #i: NO if they cannot.

## Sample Explanation

Here’s a possible strategy for the first case. Traveler 3 can carry traveler 4 across, and then return alone. Then traveler 2 can carry traveler 3 across, and then return alone. Then traveler 1 can carry traveler 2 across. This takes 5 + 5 + 2 + 2 + 1 = 15 seconds.
In the second case, there is no strategy that gets all 4 travelers across within 4 seconds.
In the third case, both travelers can cross in exactly the 22 allotted seconds if they travel together.