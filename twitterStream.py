from pyspark import SparkConf, SparkContext
from pyspark.streaming import StreamingContext
from pyspark.streaming.kafka import KafkaUtils
import operator
import numpy as np
import matplotlib.pyplot as plt


def main():
    conf = SparkConf().setMaster("local[2]").setAppName("Streamer")
    sc = SparkContext(conf=conf)
    ssc = StreamingContext(sc, 10)   # Create a streaming context with batch interval of 10 sec
    ssc.checkpoint("checkpoint")

    pwords = load_wordlist("positive.txt")
    nwords = load_wordlist("negative.txt")

    counts = stream(ssc, pwords, nwords, 100)
    #Printing the RDD before going for plotting
    print counts
    make_plot(counts)


def make_plot(counts):
    """
    Plot the counts for the positive and negative words for each timestep.
    Use plt.show() so that the plot will popup.
    """
    # YOUR CODE HERE
    #Defining diagram
    plt.xlabel('Time Step')
    plt.ylabel('Word Count')
    #plt.legend(['positive', 'negative'], loc='upper left')

    #Create lists to track count of positive and negative values
    positives = []
    negatives = []
    at = []
    num = 0

    #Add respective counts into new lists from 'counts'
    for items_in_list  in counts:
        item = items_in_list
        for key in item:
            if key[0]=='positive':
                positives.append(key[1])
                at.append(num)
            elif key[0]=='negative':
                negatives.append(key[1])
                at.append(num)
        num = num + 1

    #Updating our defined diagram
    plt.plot(positives, 'bo-', negatives, 'go-')
    max_v = max(max(positives), max(negatives))
    plt.axis([-1, num + 1, 0, max_v + 50])

    #Legend can be attached to figure once the plotting is done.
    plt.legend(['positive', 'negative'], loc='upper left')

    '''
    #Trail 2, using sub_plot
    diagram = plt.figure()
    new_axis = diagram.add_subplot(111)
    '''
    #Pop out the Plot
    plt.show()

def load_wordlist(filename):
    """
    This function should return a list or set of words from the given filename.
    """
    # YOUR CODE HERE
    print "Loading " + str(filename)

    #Reading the file containing a list in a text format and splitting it by new line
    with open(filename, 'rU') as new_file:
        new_list = new_file.read().split('\n')
        #pickle.dump(new_list, new_file)
    #print new_list
    return new_list


def stream(ssc, pwords, nwords, duration):
    kstream = KafkaUtils.createDirectStream(
        ssc, topics = ['twitterstream'], kafkaParams = {"metadata.broker.list": 'localhost:9092'})
    tweets = kstream.map(lambda x: x[1].encode("ascii","ignore"))

    # Each element of tweets will be the text of a tweet.
    # You need to find the count of all the positive and negative words in these tweets.
    # Keep track of a running total counts and print this at every time step (use the pprint function).
    # YOUR CODE HERE

    #Creating a stream object to split the text into words, map them with the incoming list of
    # positive words and negative words. Maintaining the total count of words in the stream.
    obj_words = tweets.flatMap(lambda x: x.split(' ')) \
                .map(lambda w: ('positive', 1) if w in pwords else ('negative', 1) if w in nwords else ('rest', 1)) \
                .filter(lambda c: c[0]=='positive' or c[0]=='negative').reduceByKey(lambda a, b: a + b)

    #Runtime change for the summation of the total words counted
    #runtime_value_count = obj_words.updateStateByKey(sumFunction)

    #New Sum function defined to the actual count
    def sumFunction(total_value, state):
        if state is None:
            state = 0
        return sum(total_value, state)
    #Runtime change for the summation of the total words counted
    runtime_value_count = obj_words.updateStateByKey(sumFunction)

    #Print the running count at every steps
    runtime_value_count.pprint()

    # Let the counts variable hold the word counts for all time steps
    # You will need to use the foreachRDD function.
    # For our implementation, counts looked like:
    #   [[("positive", 100), ("negative", 50)], [("positive", 80), ("negative", 60)], ...]
    counts = []
    # YOURDSTREAMOBJECT.foreachRDD(lambda t,rdd: counts.append(rdd.collect()))
    obj_words.foreachRDD(lambda t, rdd: counts.append(rdd.collect()))

    ssc.start()                         # Start the computation
    ssc.awaitTerminationOrTimeout(duration)
    ssc.stop(stopGraceFully=True)

    return counts


if __name__=="__main__":
    main()
